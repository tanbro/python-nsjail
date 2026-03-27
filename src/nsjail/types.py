from typing import Literal
from collections.abc import Mapping

StreamType = Literal["stdout", "stderr"]
NamespaceType = Literal["net", "mnt", "ipc", "uts", "pid", "user", "cgroup"]

# nsenter namespace flags
NS_FLAGS: Mapping[NamespaceType, str] = {
    "net": "-n",
    "mnt": "-m",
    "ipc": "-i",
    "uts": "-u",
    "pid": "-p",
    "user": "-U",
    "cgroup": "-C",
}
