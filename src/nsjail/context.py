"""编程式命名空间进入 (Python 3.12+ os.setns)。"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Literal

if sys.version_info >= (3, 12):
    from ._compat import setns

    __all__ = ["NamespaceContext"]
    NamespaceType = Literal["net", "mnt", "ipc", "uts", "pid", "user", "cgroup"]

    @contextmanager
    def NamespaceContext(pid: int, ns_type: NamespaceType):
        """
        编程式进入命名空间上下文管理器

        Warning:
            - 仅 Python 3.12+ 可用
            - 命名空间改变是永久的（per-thread）
            - 不能在主 server 进程中使用，必须在 worker 中使用

        Args:
            pid: 目标进程 PID
            ns_type: 命名空间类型 (net, mnt, ipc, uts, pid, user, cgroup)

        Example:
            >>> from nsjail import NamespaceContext
            >>> with NamespaceContext(1234, "net"):
            ...     # 在进程 1234 的网络命名空间中执行代码
            ...     import socket
            ...
            ...     s = socket.socket()
            ...     s.connect(("10.0.0.1", 80))
        """
        setns(pid, ns_type)
        try:
            yield
        finally:
            pass  # 无法退出命名空间
else:
    __all__ = []

    def NamespaceContext(pid: int, ns_type):
        raise NotImplementedError("NamespaceContext requires Python 3.12+")
