"""nsenter 辅助函数。"""

import shutil

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .process import NsenterProcess, NamespaceType

__all__ = ["check_nsenter", "create_nsenter_process"]

_NS_FLAGS = {
    "net": "-n",
    "mnt": "-m",
    "ipc": "-i",
    "uts": "-u",
    "pid": "-p",
    "user": "-U",
    "cgroup": "-C",
}


def check_nsenter() -> str:
    """
    检查系统是否有 nsenter 命令。

    Returns:
        nsenter 命令的路径

    Raises:
        RuntimeError: 如果 nsenter 命令不存在
    """
    nsenter_path = shutil.which("nsenter")
    if not nsenter_path:
        raise RuntimeError(
            "nsenter command not found. Install util-linux:\n"
            "  apt-get install util-linux     # Debian/Ubuntu\n"
            "  yum install util-linux         # RHEL/CentOS\n"
            "  apk add util-linux             # Alpine"
        )
    return nsenter_path


async def create_nsenter_process(
    target_pid: int,
    namespaces: list["NamespaceType"],
    command: list[str],
    options: object | None = None,
    buffer_size: int = 100,
    chunk_size: int = 1024,
    tee: bool = False,
) -> "NsenterProcess":
    """创建并启动 nsenter 进程。

    这是创建 NsenterProcess 实例的推荐方式。

    Args:
        target_pid: 目标进程的 PID
        namespaces: 要进入的命名空间类型列表 (net, mnt, ipc, uts, pid, user, cgroup)
        command: 在命名空间中执行的命令和参数
        options: NsenterOptions 实例
        buffer_size: stream() 的队列大小（最大项目数）
        chunk_size: 读取块大小（字节）
        tee: 如果为 True，在捕获输出的同时转发到控制台

    Returns:
        NsenterProcess 实例

    Raises:
        RuntimeError: 如果系统未找到 nsenter 命令

    Example:
        >>> # 在容器 1234 的网络命名空间中执行 'ip addr'
        >>> proc = await create_nsenter_process(1234, ["net"], ["ip", "addr"])
        >>> async for source, chunk in proc.stream():
        ...     if source == "stdout":
        ...         print(chunk.decode(), end="")
        >>> await proc.wait()
    """
    from .process import create_nsenter_process as _create_nsenter_process

    return await _create_nsenter_process(
        target_pid=target_pid,
        namespaces=namespaces,
        command=command,
        options=options,
        buffer_size=buffer_size,
        chunk_size=chunk_size,
        tee=tee,
    )
