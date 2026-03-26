"""Synchronous subprocess creation for nsjail and nsenter.

This module provides simple functions for creating nsjail and nsenter
subprocesses without wrapper classes.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from _typeshed import StrPath

from .locator import locate_nsjail
from .options import NsenterOptions, NsjailOptions

__all__ = (
    "create_nsjail",
    "create_nsenter",
    "build_nsjail_args",
    "build_nsenter_args",
    "NamespaceType",
)

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


# ==================== Public Helper Functions ====================


def build_nsjail_args(
    options: NsjailOptions | None = None,
    config_file: StrPath | None = None,
) -> list[str]:
    """构建 nsjail 命令行参数

    用于调试、测试或手动执行。

    Args:
        options: NsjailOptions 配置
        config_file: nsjail 配置文件路径

    Returns:
        nsjail 命令行参数列表（不含二进制路径和命令）

    Example:
        >>> args = build_nsjail_args(NsjailOptions(chroot="/"))
        >>> print(args)
        ['--chroot', '/']
    """
    args: list[str] = []
    if config_file is not None:
        args.extend(["--config", str(config_file)])
    if options is not None:
        args.extend(options.build_args())
    return args


def build_nsenter_args(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    options: NsenterOptions | None = None,
) -> list[str]:
    """构建 nsenter 命令行参数

    用于调试、测试或手动执行。

    Args:
        target_pid: 目标进程 PID
        namespaces: 要进入的命名空间列表
        options: NsenterOptions 配置

    Returns:
        nsenter 命令行参数列表（不含二进制路径和命令）

    Example:
        >>> args = build_nsenter_args(1234, ["net"])
        >>> print(args)
        ['-t', '1234', '-n']
    """
    args = ["-t", str(target_pid)]

    ns_flags = set()
    for ns in namespaces:
        flag = _NS_FLAGS.get(ns)
        if flag is None:
            raise ValueError(f"Unknown namespace type: {ns}")
        ns_flags.add(flag)
    args.extend(ns_flags)

    if options is not None:
        args.extend(options.build_args())

    return args


# ==================== Factory Functions ====================


def create_nsjail(
    command: Sequence[str],
    options: NsjailOptions | None = None,
    config_file: StrPath | None = None,
    *args,
    **kwargs,
) -> subprocess.Popen:
    """创建 nsjail 子进程（同步）

    Args:
        command: 在 nsjail 中执行的命令
        options: NsjailOptions 配置
        config_file: nsjail 配置文件路径
        *args, **kwargs: 传递给 subprocess.Popen 的其他参数

    Returns:
        subprocess.Popen 实例

    Example:
        >>> proc = create_nsjail(["/bin/echo", "hello"], stdout=subprocess.PIPE)
        >>> output, _ = proc.communicate()
    """
    nsjail_path = locate_nsjail()
    nsjail_args = build_nsjail_args(options, config_file)

    cmd = [str(nsjail_path), *nsjail_args, "--", *command]
    return subprocess.Popen(cmd, *args, **kwargs)


def create_nsenter(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    command: Sequence[str],
    options: NsenterOptions | None = None,
    *args,
    **kwargs,
) -> subprocess.Popen:
    """创建 nsenter 子进程（同步）

    Args:
        target_pid: 目标进程 PID
        namespaces: 要进入的命名空间列表
        command: 要在命名空间中执行的命令
        options: NsenterOptions 配置
        *args, **kwargs: 传递给 subprocess.Popen 的其他参数

    Returns:
        subprocess.Popen 实例

    Raises:
        RuntimeError: If nsenter command is not found

    Example:
        >>> proc = create_nsenter(1234, ["net"], ["ip", "addr"], stdout=subprocess.PIPE)
        >>> output, _ = proc.communicate()
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
    cmd = [nsenter_path, *nsenter_args, "--", *command]
    return subprocess.Popen(cmd, *args, **kwargs)
