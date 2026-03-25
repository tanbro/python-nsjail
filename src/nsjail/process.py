"""Unified process management for nsjail and nsenter.

This module provides:
- ManagedProcess: Base class for subprocess management with dual-stream support
- NsjailProcess: Alias for ManagedProcess (for backwards compatibility)
- NsenterProcess: ManagedProcess with target_pid and namespaces attributes
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import warnings
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, AsyncIterator, Literal

if sys.version_info < (3, 11):  # pragma: no cover
    from typing_extensions import Self
else:  # pragma: no cover
    from typing import Self

if TYPE_CHECKING:
    from _typeshed import StrPath

from .locator import locate_nsjail
from .options import NsenterOptions, NsjailOptions

__all__ = [
    "ManagedProcess",
    "NsjailProcess",
    "NsenterProcess",
    "create_nsjail_process",
    "create_nsenter_process",
    "StreamType",
    "NamespaceType",
]

StreamType = Literal["stdout", "stderr"]
NamespaceType = Literal["net", "mnt", "ipc", "uts", "pid", "user", "cgroup"]

# nsenter namespace flags
_NS_FLAGS = {
    "net": "-n",
    "mnt": "-m",
    "ipc": "-i",
    "uts": "-u",
    "pid": "-p",
    "user": "-U",
    "cgroup": "-C",
}

DEFAULT_BUFFER_SIZE = 256
DEFAULT_CHUNK_SIZE = 8192


# ==================== Base Class ====================


class ManagedProcess:
    """A running async sub-process wrapper with dual-stream output support.

    Note:
        Do not instantiate this class directly.

    Example:
        >>> proc = await create_nsjail_process("/bin/echo, ["hello"])
        >>> async for source, chunk in proc.stream():
        ...     print(chunk.decode())
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
            tee: If True, forward output to console in real-time (for debugging).

        Warning:
            The `tee` option uses synchronous I/O and may block if the terminal
            buffer is full. It is intended for debugging only and should not be
            used in production environments. For production use, consume output
            via :meth:`stream()` instead.
        """
        self._proc = proc
        self._chunk_size = chunk_size
        self._tee = tee

        # State management
        self._eof_received: set[StreamType] = set()

        # Reader tasks (started by factory function)
        self._read_stdout_task: asyncio.Task[None] | None = None
        self._read_stderr_task: asyncio.Task[None] | None = None

        # Create queue immediately (bounded for backpressure)
        self._queue: asyncio.Queue[tuple[StreamType, bytes]] = asyncio.Queue(
            maxsize=buffer_size
        )

        self._start_internal_read()

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
            except Exception:  # pragma: no cover
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

    async def write(self, data: bytes):
        """Write data to process stdin and wait for it to be flushed.

        Args:
            data: bytes to write.

        Raises:
            RuntimeError: If stdin is not connected.
        """
        if self._proc.stdin is None:
            raise RuntimeError("stdin is not connected (use writable_stdin=True)")
        self._proc.stdin.write(data)
        await self._proc.stdin.drain()

    def write_nowait(self, data: bytes) -> None:
        """Write data to process stdin without waiting for it to be flushed.

        Args:
            data: bytes to write.

        Raises:
            RuntimeError: If stdin is not connected.
        """
        if self._proc.stdin is None:
            raise RuntimeError("stdin is not connected (use writable_stdin=True)")
        self._proc.stdin.write(data)

    def terminate(self) -> None:
        """Gracefully stop (SIGTERM), non-blocking."""
        try:
            self._proc.terminate()
        except ProcessLookupError as e:
            warnings.warn(
                f"Process {self.pid} already terminated: {e}",
                RuntimeWarning,
                stacklevel=2,
            )

    def kill(self) -> None:
        """Force kill (SIGKILL), non-blocking."""
        try:
            self._proc.kill()
        except ProcessLookupError as e:
            warnings.warn(
                f"Process {self.pid} already dead: {e}",
                RuntimeWarning,
                stacklevel=2,
            )

    async def aclose(self, timeout: float | None = 5) -> None:
        """Explicit close, terminate with timeout fallback to kill.

        Args:
            timeout: Seconds to wait after terminate before killing.
        """
        if self.is_running():
            self.terminate()
            try:
                await asyncio.wait_for(self.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                self.kill()
        # Always wait for reader tasks to complete
        await self._wait_readers()

    # ===== Output handling =====

    async def stream(self) -> AsyncIterator[tuple[StreamType, bytes]]:
        """Stream stdout/stderr with preserved ordering.

        Call this method once and consume the iterator fully.
        Cannot be called after both streams have reached EOF.

        Yields:
            (source, chunk): source is "stdout" or "stderr", chunk is bytes

        Raises:
            RuntimeError: If all output has already been consumed
                (both streams reached EOF).
        """
        # Check if all output has already been consumed
        if len(self._eof_received) > 1:
            raise RuntimeError(
                "Cannot stream() after all output has been consumed (both streams reached EOF)"
            )

        while True:
            source, chunk = await self._queue.get()
            if not chunk:  # EOF marker
                # Check if both streams are done
                if len(self._eof_received) > 1:
                    break
                continue
            yield (source, chunk)

    # ===== Private methods =====

    def _start_internal_read(self) -> None:
        """Start stdout/stderr reader tasks."""
        self._read_stdout_task = asyncio.create_task(self._internal_read("stdout"))
        self._read_stderr_task = asyncio.create_task(self._internal_read("stderr"))

    async def _internal_read(self, source: StreamType) -> None:
        """Read stdout or stderr stream.

        Data flow:
        - If tee=True: print to console and optionally queue for stream()
        - If streaming: put into queue, discard oldest when full (ring buffer)
        """
        if (
            stream := self._proc.stdout if source == "stdout" else self._proc.stderr
        ) is None:  # pragma: no cover
            raise RuntimeError(f"{source} stream is None")

        while True:
            if not (chunk := await stream.read(self._chunk_size)):
                # EOF: put marker and update global state
                self._eof_received.add(source)
                try:
                    self._queue.put_nowait((source, b""))
                except asyncio.QueueFull:
                    # Queue full, discard oldest item to make room for EOF
                    self._queue.get_nowait()
                    self._queue.put_nowait((source, b""))
                break

            # Always queue data (non-blocking, discard oldest when full)
            # This allows stream() to be called at any time and get recent data
            # Discard oldest item to make room if full
            if self._queue.full():
                self._queue.get_nowait()
            self._queue.put_nowait((source, chunk))

            # Tee to console
            if self._tee:  # pragma: no cover
                if source == "stderr":
                    print(chunk.decode(), end="", file=sys.stderr)
                else:
                    print(chunk.decode(), end="")

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


# ==================== Subclasses ====================
class NsjailProcess(ManagedProcess):
    pass


class NsenterProcess(ManagedProcess):
    """Process running inside another container's namespace via nsenter.

    Attributes:
        target_pid: PID of the target process whose namespace we're entering
        namespaces: List of namespace types being entered
    """

    def __init__(
        self,
        proc: asyncio.subprocess.Process,
        target_pid: int,
        namespaces: list[NamespaceType],
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        tee: bool = False,
    ):
        """Initialize NsenterProcess.

        Args:
            proc: The underlying asyncio subprocess
            target_pid: PID of the target process
            namespaces: List of namespace types being entered
            buffer_size: Queue size for stream()
            chunk_size: Read chunk size in bytes
            tee: Whether to tee output to console
        """
        self._target_pid = target_pid
        self._namespaces = namespaces

        super().__init__(proc, buffer_size, chunk_size, tee)

    @property
    def target_pid(self) -> int:
        """PID of the target process."""
        return self._target_pid

    @property
    def namespaces(self) -> list[NamespaceType]:
        """List of namespace types being entered."""
        return self._namespaces


# ==================== Factory Functions ====================


async def create_nsjail_process(
    command: Sequence[str],
    options: NsjailOptions | None = None,
    config_file: StrPath | None = None,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    tee: bool = False,
    writable_stdin: bool = False,
) -> NsjailProcess:
    """Create and start an nsjail process.

    This is the recommended way to create a :class:`NsjailProcess` instance.
    Do not call :class:`NsjailProcess` constructor directly.

    Args:
        command: Command and arguments to execute inside nsjail (e.g. ["/bin/echo", "hello"])
        options: NsjailOptions instance
        config_file: Path to nsjail config file (applied before options, can be overridden)
        buffer_size: Queue size for stream read (max items)
        chunk_size: Read chunk size in bytes
        tee: If True, forward output to console while still capturing for stream()
        writable_stdin: If True, connect stdin to allow writing via write()

    Returns:
        NsjailProcess instance

    Example:
        >>> proc = await create_nsjail_process(
        ...     command=["/bin/echo", "hello"],
        ...     options=NsjailOptions(chroot="/"),
        ... )
        >>> await proc.wait()
    """

    # Find nsjail binary
    nsjail_path = locate_nsjail()
    # Build command
    nsjail_args = []

    # Config file first (allows override by later options)
    if config_file is not None:
        nsjail_args.extend(["--config", str(config_file)])

    if options is not None:
        nsjail_args.extend(options.build_args())

    # Start subprocess
    stdin_arg = asyncio.subprocess.PIPE if writable_stdin else None
    proc = await asyncio.create_subprocess_exec(
        nsjail_path,
        *(nsjail_args + ["--"] + list(command)),
        stdin=stdin_arg,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Create wrapper and start readers
    nsjail_proc = NsjailProcess(
        proc, buffer_size=buffer_size, chunk_size=chunk_size, tee=tee
    )

    return nsjail_proc


async def create_nsenter_process(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    command: Sequence[str],
    options: NsenterOptions | None = None,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    tee: bool = False,
    writable_stdin: bool = False,
) -> NsenterProcess:
    """Create and start a process inside another container's namespace via nsenter.

    This uses the system's nsenter command (from util-linux) to execute commands
    inside the Linux namespaces of a target process.

    Args:
        target_pid: PID of the target process whose namespace to enter
        namespaces: List of namespace types to enter (net, mnt, ipc, uts, pid, user, cgroup)
        command: Command and arguments to execute inside the namespace
        options: NsenterOptions instance
        buffer_size: Queue size for stream read (max items)
        chunk_size: Read chunk size in bytes
        tee: If True, forward output to console while still capturing for stream()
        writable_stdin: If True, connect stdin to allow writing via write()

    Returns:
        NsenterProcess instance

    Raises:
        RuntimeError: If nsenter command is not found on the system

    Example:
        >>> # Run 'ip addr' inside container 1234's network namespace
        >>> proc = await create_nsenter_process(1234, ["net"], ["ip", "addr"])
        >>> async for source, chunk in proc.stream():
        ...     if source == "stdout":
        ...         print(chunk.decode(), end="")
        >>> await proc.wait()
    """
    # Check nsenter availability
    nsenter_path = shutil.which("nsenter")
    if not nsenter_path:
        raise RuntimeError(
            "nsenter command not found. Install util-linux:\n"
            "  apt install util-linux     # Debian/Ubuntu\n"
            "  yum install util-linux         # RHEL/CentOS\n"
            "  apk add util-linux             # Alpine"
        )

    # Build nsenter command
    nsenter_args = ["-t", str(target_pid)]
    ns_flags = set()
    for ns in namespaces:
        if (flag := _NS_FLAGS.get(ns)) is None:
            raise ValueError(f"Unknown namespace type: {ns}")
        ns_flags.add(flag)
    nsenter_args.extend(ns_flags)

    # Add options
    if options is not None:
        nsenter_args.extend(options.build_args())

    # Start subprocess
    proc = await asyncio.create_subprocess_exec(
        nsenter_path,
        *(nsenter_args + ["--"] + list(command)),
        stdin=asyncio.subprocess.PIPE if writable_stdin else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Create and return wrapper
    return NsenterProcess(
        proc,
        target_pid=target_pid,
        namespaces=list(namespaces),
        buffer_size=buffer_size,
        chunk_size=chunk_size,
        tee=tee,
    )
