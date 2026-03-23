"""Async process management for nsjail."""

from __future__ import annotations

import asyncio
import sys
from collections import deque
from typing import AsyncIterator, Literal

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .find import find_bundled_nsjail, find_system_nsjail
from .options import NsjailOptions

__all__ = ["NsjailProcess", "start"]

StreamSource = Literal["stdout", "stderr"]


class RingBuffer:
    """Fixed-size ring buffer for async streaming."""

    def __init__(self, maxsize: int | None = None):
        self._buffer: deque[tuple[StreamSource, bytes]] = deque(maxlen=maxsize)
        self._not_empty = asyncio.Condition()

    async def put(self, source: StreamSource, item: bytes) -> None:
        """Put an item into the buffer."""
        async with self._not_empty:
            self._buffer.append((source, item))
            self._not_empty.notify(1)

    async def get(self) -> tuple[StreamSource, bytes]:
        """Get an item from the buffer, blocking if empty."""
        async with self._not_empty:
            while len(self._buffer) == 0:
                await self._not_empty.wait()
            return self._buffer.popleft()

    def qsize(self) -> int:
        """Return approximate size of the buffer."""
        return len(self._buffer)


class NsjailProcess:
    """A running nsjail process with dual-stream output support."""

    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        auto_print: bool = False,
        buffer_size: int = 1024,
        chunk_size: int = 4096,
    ):
        self._proc = proc
        self._auto_print = auto_print
        self._buffer_size = buffer_size
        self._chunk_size = chunk_size

        # Lazy-initialized on first stream() call
        self._internal_read_buffer = RingBuffer(maxsize=self._buffer_size)
        self._streaming = False
        self._stderr_eof_received = False

        # Reader tasks
        self._read_stdout_task: asyncio.Task[None] | None = None
        self._read_stderr_task: asyncio.Task[None] | None = None

        #
        self._start_internal_read()

    @property
    def pid(self) -> int:
        """nsjail process PID."""
        return self._proc.pid

    @property
    def returncode(self) -> int | None:
        """None if running, otherwise exit code."""
        return self._proc.returncode

    def is_running(self) -> bool:
        """Whether the process is still running."""
        return self._proc.returncode is None

    async def wait(self) -> int:
        """Wait for process to finish, return exit code."""
        return await self._proc.wait()

    def terminate(self) -> None:
        """Gracefully stop (SIGTERM), non-blocking."""
        self._proc.terminate()

    def kill(self) -> None:
        """Force kill (SIGKILL), non-blocking."""
        self._proc.kill()

    async def stream(self) -> AsyncIterator[tuple[str, bytes]]:
        """Stream stdout/stderr.

        Yields:
            (source, chunk): source is "stdout" or "stderr", chunk is bytes

        Note:
            First call activates ring buffers. Previous data is discarded.
            Full buffer overwrites old data (circular).
        """
        if not self._streaming:
            self._streaming = True

        # Iterate until both streams send EOF marker
        while True:
            source, chunk = await self._internal_read_buffer.get()
            if not chunk:  # EOF marker
                # Wait for both streams to finish
                if source == "stdout" and self._stderr_eof_received:
                    break
                elif source == "stderr":
                    self._stderr_eof_received = True
                continue
            yield (source, chunk)

    def _start_internal_read(self) -> None:
        self._read_stdout_task = asyncio.create_task(self._interal_read("stdout"))
        self._read_stderr_task = asyncio.create_task(self._interal_read("stderr"))

    async def _interal_read(self, source: StreamSource) -> None:
        """Read stdout or stderr stream."""
        stream = self._proc.stdout if source == "stdout" else self._proc.stderr
        if stream is None:
            raise RuntimeError(f"{source} stream is None")

        while True:
            chunk = await stream.read(self._chunk_size)
            if not chunk:
                # EOF: put empty bytes marker
                if self._streaming and self._internal_read_buffer:
                    await self._internal_read_buffer.put(source, b"")
                break
            # Optional print
            if self._auto_print:
                if source == "stderr":
                    print(chunk.decode(), end="", file=sys.stderr)
                else:
                    print(chunk.decode(), end="")
            # Buffer if streaming
            if self._streaming and self._internal_read_buffer:
                await self._internal_read_buffer.put(source, chunk)

    async def __aenter__(self) -> Self:
        """Enter context manager."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit context manager, calls terminate() + wait()."""
        await self.aclose()

    async def aclose(self, timeout: int = 5) -> None:
        """Explicit close, terminate with timeout fallback to kill.

        Args:
            timeout: Seconds to wait after terminate before killing.
        """
        self.terminate()
        try:
            await asyncio.wait_for(self.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            self.kill()


async def start(
    command: str,
    args: list[str] | None = None,
    options: object | None = None,  # NsjailOptions, but avoid circular import
    auto_print: bool = False,
    buffer_size: int = 1024,
    chunk_size: int = 4096,
) -> NsjailProcess:
    """Start an nsjail process.

    Args:
        command: Command to execute inside nsjail
        args: Command arguments
        options: NsjailOptions instance
        auto_print: Whether to auto-print output
        buffer_size: Ring buffer size for stream()

    Returns:
        NsjailProcess instance
    """

    # Find nsjail binary
    nsjail_bin = find_system_nsjail() or find_bundled_nsjail()
    if nsjail_bin is None:
        raise RuntimeError("nsjail binary not found")

    # Build command
    cmd_args: list[str] = [str(nsjail_bin)]

    if options is not None:
        if isinstance(options, NsjailOptions):
            cmd_args.extend(options.build_args())
        else:
            raise TypeError(f"options must be NsjailOptions, not {type(options)}")

    # Separator and command
    cmd_args.append("--")
    cmd_args.append(command)
    if args:
        cmd_args.extend(args)

    # Start subprocess
    proc = await asyncio.create_subprocess_exec(
        *cmd_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Create wrapper
    nsjail_proc = NsjailProcess(
        proc, auto_print=auto_print, buffer_size=buffer_size, chunk_size=chunk_size
    )

    return nsjail_proc
