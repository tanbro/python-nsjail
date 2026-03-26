"""Asynchronous subprocess creation for nsjail and nsenter.

This module provides simple async functions for creating nsjail and nsenter
subprocesses without wrapper classes.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import AsyncIterator, Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath

from .locator import locate_nsjail
from .options import NsenterOptions, NsjailOptions
from .subprocess import build_nsenter_args, build_nsjail_args
from .types import StreamType, NamespaceType

__all__ = ("async_create_nsjail", "async_create_nsenter", "merge_streams")


# ==================== Factory Functions ====================


async def async_create_nsjail(
    command: Sequence[str],
    options: NsjailOptions | None = None,
    config: StrPath | None = None,
    **kwargs,
) -> asyncio.subprocess.Process:
    """Create nsjail subprocess (asynchronous).

    Args:
        command: Command to execute inside nsjail
        options: NsjailOptions configuration
        config: Path to nsjail config file
        **kwargs: Additional arguments passed to :func:`asyncio.create_subprocess_exec`

    Returns:
        asyncio.subprocess.Process instance

    Example:
        >>> proc = await async_create_nsjail(["/bin/echo", "hello"], stdout=PIPE)
        >>> async for line in proc.stdout:
        ...     print(line.decode(), end="")
    """
    nsjail_path = locate_nsjail()
    nsjail_args = build_nsjail_args(options, config)

    return await asyncio.create_subprocess_exec(
        nsjail_path, *nsjail_args, "--", *command, **kwargs
    )


async def async_create_nsenter(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    command: Sequence[str],
    options: NsenterOptions | None = None,
    **kwargs,
) -> asyncio.subprocess.Process:
    """Create nsenter subprocess (asynchronous).

    Args:
        target_pid: Target process PID
        namespaces: List of namespace types to enter
        command: Command to execute inside the namespace
        options: NsenterOptions configuration
        **kwargs: Additional arguments passed to :func:`asyncio.create_subprocess_exec`

    Returns:
        asyncio.subprocess.Process instance

    Raises:
        RuntimeError: If nsenter command is not found

    Example:
        >>> proc = await async_create_nsenter(
        ...     1234, ["net"], ["ip", "addr"], stdout=PIPE
        ... )
        >>> async for line in proc.stdout:
        ...     print(line.decode(), end="")
    """
    nsenter_path = shutil.which("nsenter")
    if not nsenter_path:
        raise RuntimeError(
            "nsenter command not found. Install util-linux:\n"
            "  apt install util-linux     # Debian/Ubuntu\n"
            "  yum install util-linux         # RHEL/CentOS\n"
            "  apk add util-linux             # Alpine"
        )

    nsenter_args = build_nsenter_args(target_pid, namespaces, options)
    return await asyncio.create_subprocess_exec(
        nsenter_path, *nsenter_args, "--", *command, **kwargs
    )


# ==================== Utility Functions ====================


async def merge_streams(
    proc: asyncio.subprocess.Process,
    chunk_size: int = 8192,
    stdout: bool = True,
    stderr: bool = True,
) -> AsyncIterator[tuple[StreamType, bytes]]:
    """Merge stdout/stderr streams utility function.

    Args:
        proc: asyncio subprocess instance
        chunk_size: Number of bytes to read per chunk
        stdout: Whether to read from stdout
        stderr: Whether to read from stderr

    Yields:
        (source, chunk): source is "stdout" or "stderr", chunk is bytes

    Raises:
        RuntimeError: If no streams are available

    Warning:
        If the subprocess continues producing output while the caller exits
        the loop early, the subprocess may block. Ensure proper process
        lifecycle management (use try/finally or async with).

    Example:
        >>> proc = await async_create_nsjail(
        ...     ["/bin/cat", "file"], stdout=PIPE, stderr=PIPE
        ... )
        >>> async for source, chunk in merge_streams(proc):
        ...     if source == "stdout":
        ...         print(chunk.decode(), end="")
    """
    streams: dict[StreamType, asyncio.StreamReader] = {}
    if stdout and (s := proc.stdout):
        streams["stdout"] = s
    if stderr and (s := proc.stderr):
        streams["stderr"] = s

    if not streams:
        raise RuntimeError("No streams available")

    while streams:
        # Create tasks for each active stream
        tasks: dict[StreamType, asyncio.Task[bytes]] = {
            name: asyncio.create_task(stream.read(chunk_size))
            for name, stream in streams.items()
        }

        # Wait for first one to complete
        done, pending = await asyncio.wait(
            tasks.values(), return_when=asyncio.FIRST_COMPLETED
        )

        # Find and yield the completed result
        for name, task in tasks.items():
            if task in done:
                chunk = task.result()
                if not chunk:  # EOF
                    del streams[name]
                else:
                    yield name, chunk
                break

        # Cancel pending tasks (safe for StreamReader)
        for task in pending:
            task.cancel()
