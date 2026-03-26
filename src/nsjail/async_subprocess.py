"""Asynchronous subprocess creation for nsjail and nsenter.

This module provides simple async functions for creating nsjail and nsenter
subprocesses without wrapper classes.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import AsyncIterator, Iterable, Sequence
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from _typeshed import StrPath

from .locator import locate_nsjail
from .options import NsenterOptions, NsjailOptions
from .subprocess import NamespaceType, build_nsenter_args, build_nsjail_args

__all__ = [
    "async_create_nsjail",
    "async_create_nsenter",
    "merge_streams",
    "StreamType",
]

StreamType = Literal["stdout", "stderr"]


# ==================== Factory Functions ====================


async def async_create_nsjail(
    command: Sequence[str],
    options: NsjailOptions | None = None,
    config_file: StrPath | None = None,
    *args,
    **kwargs,
) -> asyncio.subprocess.Process:
    """创建 nsjail 子进程（异步）

    Args:
        command: 在 nsjail 中执行的命令
        options: NsjailOptions 配置
        config_file: nsjail 配置文件路径
        *args, **kwargs: 传递给 asyncio.create_subprocess_exec 的其他参数

    Returns:
        asyncio.subprocess.Process 实例

    Example:
        >>> proc = await async_create_nsjail(["/bin/echo", "hello"], stdout=PIPE)
        >>> async for line in proc.stdout:
        ...     print(line.decode(), end="")
    """
    nsjail_path = locate_nsjail()
    nsjail_args = build_nsjail_args(options, config_file)

    return await asyncio.create_subprocess_exec(
        nsjail_path,
        *nsjail_args,
        "--",
        *command,
        *args,
        **kwargs,
    )


async def async_create_nsenter(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    command: Sequence[str],
    options: NsenterOptions | None = None,
    *args,
    **kwargs,
) -> asyncio.subprocess.Process:
    """创建 nsenter 子进程（异步）

    Args:
        target_pid: 目标进程 PID
        namespaces: 要进入的命名空间列表
        command: 要在命名空间中执行的命令
        options: NsenterOptions 配置
        *args, **kwargs: 传递给 asyncio.create_subprocess_exec 的其他参数

    Returns:
        asyncio.subprocess.Process 实例

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
        nsenter_path,
        *nsenter_args,
        "--",
        *command,
        *args,
        **kwargs,
    )


# ==================== Utility Functions ====================


async def merge_streams(
    proc: asyncio.subprocess.Process,
    chunk_size: int = 8192,
    stdout: bool = True,
    stderr: bool = True,
) -> AsyncIterator[tuple[StreamType, bytes]]:
    """合并 stdout/stderr 的便利函数

    Args:
        proc: asyncio subprocess 实例
        chunk_size: 每次读取的块大小
        stdout: 是否读取 stdout
        stderr: 是否读取 stderr

    Yields:
        (source, chunk): source 是 "stdout" 或 "stderr"，chunk 是 bytes

    Raises:
        RuntimeError: If no streams are available

    Warning:
        如果子进程持续输出而调用者提前退出循环，子进程可能会阻塞。
        请确保正确处理进程生命周期（使用 try/finally 或 async with）。

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
        tasks = {
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
