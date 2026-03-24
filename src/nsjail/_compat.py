"""兼容层：setns syscall 包装。"""

from __future__ import annotations

import ctypes
import os
from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from typing import Any

NamespaceType = Literal["net", "mnt", "ipc", "uts", "pid", "user", "cgroup"]

_CLONE_FLAGS = {
    "net": 0x40000000,
    "mnt": 0x00020000,
    "ipc": 0x08000000,
    "uts": 0x04000000,
    "pid": 0x20000000,
    "user": 0x10000000,
    "cgroup": 0x02000000,
}

_setns_fn: Callable[[int, int], Any]

# 使用 Python 3.12+ 的 os.setns
if hasattr(os, "setns"):
    _setns_fn = os.setns
else:
    # Fallback to ctypes
    try:
        _libc = ctypes.CDLL("libc.so.6", use_errno=True)
        _libc.setns.argtypes = [ctypes.c_int, ctypes.c_int]
        _libc.setns.restype = ctypes.c_int

        def _setns_fn(fd: int, nstype: int) -> None:
            result = _libc.setns(fd, nstype)
            if result == -1:
                e = ctypes.get_errno()
                raise OSError(e, os.strerror(e))
    except OSError:
        # 最后的 fallback

        def _setns_fn(fd: int, nstype: int) -> None:
            raise NotImplementedError("setns not available")


def setns(pid: int, ns_type: NamespaceType) -> None:
    """
    进入目标进程的命名空间

    Args:
        pid: 目标进程 PID
        ns_type: 命名空间类型 (net, mnt, ipc, uts, pid, user, cgroup)
    """
    ns_path = f"/proc/{pid}/ns/{ns_type}"
    fd = os.open(ns_path, os.O_RDONLY)
    try:
        flag = _CLONE_FLAGS[ns_type]
        _setns_fn(fd, flag)
    finally:
        os.close(fd)
