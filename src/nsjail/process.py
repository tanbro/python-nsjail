"""Async process management for nsjail."""

from __future__ import annotations

import asyncio
import sys
import warnings
from typing import AsyncIterator, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath
if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from .find import find_bundled_nsjail, find_system_nsjail
from .options import NsjailOptions

__all__ = ["NsjailProcess", "create_nsjail_process", "StreamSource"]

StreamSource = Literal["stdout", "stderr"]


class NsjailProcess:
    """A running nsjail process with dual-stream output support.

    Uses a single asyncio.Queue to preserve output ordering between stdout and stderr.
    Queue is lazily created on first stream() call.

    Note:
        Do not instantiate this class directly. Use :func:`create_nsjail_process` instead.
    """

    # ===== Special methods =====

    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        buffer_size: int,
        chunk_size: int,
        tee: bool,
    ):
        """Initialize NsjailProcess.

        Note::
            Do not call this constructor directly. Use :func:`create_nsjail_process` instead.

        Args:
            proc: The underlying asyncio subprocess
            buffer_size: Queue size for stream()
            chunk_size: Read chunk size in bytes
            tee: Whether to tee output to console
        """
        self._proc = proc
        self._chunk_size = chunk_size
        self._tee = tee

        self._streaming = False
        self._stderr_eof_received = False

        # Reader tasks (started by factory function)
        self._read_stdout_task: asyncio.Task[None] | None = None
        self._read_stderr_task: asyncio.Task[None] | None = None

        # Create queue immediately (bounded for backpressure)
        self._queue: asyncio.Queue[tuple[StreamSource, bytes]] = asyncio.Queue(
            maxsize=buffer_size
        )

    def __del__(self) -> None:
        """Warn if process was not properly closed."""
        if self.is_running():
            try:
                warnings.warn(
                    f"NsjailProcess {self.pid} was not closed. "
                    "Use 'async with' or 'await proc.aclose()'",
                    ResourceWarning,
                    source=self,
                )
            except Exception:
                pass  # __del__ must not raise
            finally:
                self.kill()

    async def __aenter__(self) -> Self:
        """Enter context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager, calls terminate() + wait()."""
        _ = exc_type, exc_val, exc_tb  # Unused but required by protocol
        await self.aclose()

    # ===== Properties =====

    @property
    def pid(self) -> int:
        """nsjail process PID."""
        return self._proc.pid

    @property
    def returncode(self) -> int | None:
        """None if running, otherwise exit code."""
        return self._proc.returncode

    # ===== State query =====

    def is_running(self) -> bool:
        """Whether the process is still running."""
        return self._proc.returncode is None

    # ===== Process control =====

    async def wait(self) -> int:
        """Wait for process to finish, return exit code."""
        return await self._proc.wait()

    def terminate(self) -> None:
        """Gracefully stop (SIGTERM), non-blocking."""
        self._proc.terminate()

    def kill(self) -> None:
        """Force kill (SIGKILL), non-blocking."""
        self._proc.kill()

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
        finally:
            # Always wait for reader tasks to complete
            await self._wait_readers()

    # ===== Output handling =====

    async def stream(self) -> AsyncIterator[tuple[StreamSource, bytes]]:
        """Stream stdout/stderr with preserved ordering.

        Yields:
            (source, chunk): source is "stdout" or "stderr", chunk is bytes

        Note:
            First call activates streaming. Previous data is discarded.
            Queue is bounded (maxsize=buffer_size); put() blocks when full.
        """
        self._streaming = True

        # Iterate until both streams send EOF marker
        while True:
            source, chunk = await self._queue.get()
            if not chunk:  # EOF marker
                # Wait for both streams to finish
                if source == "stdout" and self._stderr_eof_received:
                    break
                elif source == "stderr":
                    self._stderr_eof_received = True
                continue
            yield (source, chunk)

    # ===== Private methods =====

    def _start_internal_read(self) -> None:
        """Start stdout/stderr reader tasks."""
        self._read_stdout_task = asyncio.create_task(self._internal_read("stdout"))
        self._read_stderr_task = asyncio.create_task(self._internal_read("stderr"))

    async def _internal_read(self, source: StreamSource) -> None:
        """Read stdout or stderr stream.

        Data flow:
        - If tee=True: print to console and optionally queue for stream()
        - If streaming: put into queue, discard oldest when full (ring buffer)
        """
        stream = self._proc.stdout if source == "stdout" else self._proc.stderr
        if stream is None:
            raise RuntimeError(f"{source} stream is None")

        while True:
            chunk = await stream.read(self._chunk_size)
            if not chunk:
                # EOF: put empty bytes marker
                if self._streaming:
                    await self._queue.put((source, b""))
                break

            # Tee to console
            if self._tee:
                if source == "stderr":
                    print(chunk.decode(), end="", file=sys.stderr)
                else:
                    print(chunk.decode(), end="")

            # Queue if streaming (non-blocking, discard oldest when full)
            if self._streaming:
                # Discard oldest item to make room if full
                if self._queue.full():
                    self._queue.get_nowait()
                self._queue.put_nowait((source, chunk))

    async def _wait_readers(self) -> None:
        """Wait for stdout/stderr reader tasks to complete."""
        # Collect pending tasks
        tasks = []
        if self._read_stdout_task is not None and not self._read_stdout_task.done():
            tasks.append(self._read_stdout_task)
        if self._read_stderr_task is not None and not self._read_stderr_task.done():
            tasks.append(self._read_stderr_task)

        if not tasks:
            return

        # Cancel and wait
        for task in tasks:
            task.cancel()

        # Wait for cancellation to take effect (ignore CancelledError)
        await asyncio.gather(*tasks, return_exceptions=True)


async def create_nsjail_process(
    command: str,
    args: list[str] | None = None,
    options: object | None = None,
    config_file: StrPath | None = None,
    buffer_size: int = 256,
    chunk_size: int = 65536,
    tee: bool = False,
) -> NsjailProcess:
    """Create and start an nsjail process.

    This is the recommended way to create a :class:`NsjailProcess` instance.
    Do not call :class:`NsjailProcess` constructor directly.

    Args:
        command: Command to execute inside nsjail
        args: Command arguments
        options: NsjailOptions instance
        config_file: Path to nsjail config file (applied before options, can be overridden)
        buffer_size: Queue size for stream read (max items)
        chunk_size: Read chunk size in bytes
        tee: If True, forward output to console while still capturing for stream()

    Returns:
        NsjailProcess instance

    Example:
        >>> proc = await create_nsjail_process(
        ...     command="/bin/echo",
        ...     args=["hello"],
        ...     options=NsjailOptions(chroot="/"),
        ... )
        >>> await proc.wait()
    """

    # Find nsjail binary
    nsjail_bin = find_system_nsjail() or find_bundled_nsjail()
    if nsjail_bin is None:
        raise RuntimeError("nsjail binary not found")

    # Build command
    cmd_args: list[str] = [str(nsjail_bin)]

    # Config file first (allows override by later options)
    if config_file is not None:
        cmd_args.extend(["--config", str(config_file)])

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
        proc, tee=tee, buffer_size=buffer_size, chunk_size=chunk_size
    )

    # Start readers (explicit, not in __init__)
    nsjail_proc._start_internal_read()

    return nsjail_proc
