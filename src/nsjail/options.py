"""nsjail and nsenter command line options."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from enum import Enum

from .types import ProcessOptionsProtocol


__all__ = ["NsjailMode", "NsjailOptions", "NsenterOptions"]


class NsjailMode(str, Enum):
    """nsjail execution modes.

    See nsjail --help for details.
    """

    ONCE = "o"
    """MODE_STANDALONE_ONCE: Launch with clone/execve, parent monitors child (default)."""

    EXECVE = "e"
    """MODE_STANDALONE_EXECVE: Direct execve, no parent process (limits not enforced)."""

    RERUN = "r"
    """MODE_STANDALONE_RERUN: Like ONCE but restart forever."""

    LISTEN = "l"
    """MODE_LISTEN_TCP: TCP listen mode, requires --port."""


@dataclass
class NsjailOptions(ProcessOptionsProtocol):
    """nsjail command line options (arguments before '--')."""

    # Execution mode
    mode: NsjailMode | str | None = None  # --mode|-M

    # Filesystem
    chroot: str | None = None  # --chroot DIR
    cwd: str | None = None  # --cwd DIR
    hostname: str | None = None  # --hostname HOSTNAME

    # Bind mounts (--bindmount_ro, --bindmount)
    # Supports 'source' or 'source:dest' syntax
    bindmount_ro: Sequence[str] | None = None  # read-only bind mounts
    bindmount: Sequence[str] | None = None  # read-write bind mounts

    # Tmpfs mounts (--tmpfsmount)
    # Supports 'dest' syntax
    tmpfsmount: Sequence[str] | None = None

    # User/Group
    user: str | int | None = None  # --user UID
    group: str | int | None = None  # --group GID

    # Environment
    clear_env: bool | None = None  # None=don't pass, True=--keep_env=false
    env: Mapping[str, str] | None = None  # None/empty=don't pass, else --env k=v

    # Resource limits
    time_limit: int | None = None  # --time_limit SEC (wall time)
    cpu_time_limit: int | None = None  # --rlimit_cpu SEC (CPU time)
    memory_limit: int | None = None  # --rlimit_as MB
    max_cpus: int | None = None  # --max_cpus N
    max_pids: int | None = None  # --cgroup_pids_max N
    max_open_files: int | None = None  # --rlimit_nofile N

    # Namespace control
    disable_clone_newnet: bool | None = None
    disable_clone_newuser: bool | None = None
    disable_clone_newpid: bool | None = None

    def build_args(self) -> Sequence[str]:
        """Build nsjail command line argument list.

        Rules:
        - None values don't generate arguments
        - Empty containers ({}, []) don't generate arguments
        - Other values (including "", 0, False) generate corresponding arguments
        - Uses long format for all options (e.g. --chroot, not -c)
        """
        args: list[str] = []

        # Execution mode
        if self.mode is not None:
            value = self.mode.value if isinstance(self.mode, NsjailMode) else self.mode
            args.extend(["--mode", value])

        # Filesystem
        if self.chroot is not None:
            args.extend(["--chroot", self.chroot])
        if self.cwd is not None:
            args.extend(["--cwd", self.cwd])
        if self.hostname is not None:
            args.extend(["--hostname", self.hostname])

        # Bind mounts
        if self.bindmount_ro:
            for bind in self.bindmount_ro:
                args.extend(["--bindmount_ro", bind])
        if self.bindmount:
            for bind in self.bindmount:
                args.extend(["--bindmount", bind])

        # Tmpfs mounts
        if self.tmpfsmount:
            for dst in self.tmpfsmount:
                args.extend(["--tmpfsmount", dst])

        # User/Group
        if self.user is not None:
            args.extend(["--user", str(self.user)])
        if self.group is not None:
            args.extend(["--group", str(self.group)])

        # Environment
        if self.clear_env is not None:
            if self.clear_env:
                args.append("--keep_env=false")
            else:
                args.append("--keep_env=true")
        if self.env:
            for k, v in self.env.items():
                args.extend(["--env", f"{k}={v}"])

        # Resource limits
        if self.time_limit is not None:
            args.extend(["--time_limit", str(self.time_limit)])
        if self.cpu_time_limit is not None:
            args.extend(["--rlimit_cpu", str(self.cpu_time_limit)])
        if self.memory_limit is not None:
            args.extend(["--rlimit_as", str(self.memory_limit)])
        if self.max_cpus is not None:
            args.extend(["--max_cpus", str(self.max_cpus)])
        if self.max_pids is not None:
            args.extend(["--cgroup_pids_max", str(self.max_pids)])
        if self.max_open_files is not None:
            args.extend(["--rlimit_nofile", str(self.max_open_files)])

        # Namespace control
        if self.disable_clone_newnet:
            args.append("--disable_clone_newnet")
        if self.disable_clone_newuser:
            args.append("--disable_clone_newuser")
        if self.disable_clone_newpid:
            args.append("--disable_clone_newpid")

        return args


@dataclass
class NsenterOptions(ProcessOptionsProtocol):
    """nsenter command line options.

    nsenter is used to enter the namespaces of a target process and execute
    a command. These options control how the namespaces are entered.
    """

    # Working directory
    wd: str | None = None  # --wd PATH

    # Root filesystem
    root: str | None = None  # --root DIR

    # User/Group
    user: str | None = None  # --user USER
    group: str | None = None  # --group GROUP

    # Credentials
    preserve_credentials: bool = False  # --preserve-credentials

    # Environment
    env: Mapping[str, str] | None = None  # --env K=V

    def build_args(self) -> Sequence[str]:
        """Build nsenter command line argument list.

        Rules:
        - None values don't generate arguments
        - Empty containers ({}, []) don't generate arguments
        - Other values (including "", 0, False) generate corresponding arguments
        - Uses long format for all options
        """
        args: list[str] = []

        # Working directory
        if self.wd is not None:
            args.extend(["--wd", self.wd])

        # Root filesystem
        if self.root is not None:
            args.extend(["--root", self.root])

        # User/Group
        if self.user is not None:
            args.extend(["--user", self.user])
        if self.group is not None:
            args.extend(["--group", self.group])

        # Credentials
        if self.preserve_credentials:
            args.append("--preserve-credentials")

        # Environment
        if self.env:
            for k, v in self.env.items():
                args.extend(["--env", f"{k}={v}"])

        return args
