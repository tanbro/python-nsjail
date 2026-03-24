"""nsjail command line options."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping, Sequence


__all__ = ["NsjailOptions"]


@dataclass
class NsjailOptions:
    """nsjail command line options (arguments before '--').

    Execution mode is fixed to ONCE (-Mo), mode parameter is not exposed.
    """

    # Filesystem
    chroot: str | None = None  # --chroot DIR
    cwd: str | None = None  # --cwd DIR

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
        - Always adds -Mo (ONCE mode)
        - Uses long format for all options (e.g. --chroot, not -c)
        """
        args: list[str] = []

        # Always use ONCE mode (keep short format, it's stable)
        args.append("-Mo")

        # Filesystem
        if self.chroot is not None:
            args.extend(["--chroot", self.chroot])
        if self.cwd is not None:
            args.extend(["--cwd", self.cwd])

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
