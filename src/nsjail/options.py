"""nsjail command line options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

__all__ = ["NsjailOptions"]


@dataclass
class NsjailOptions:
    """nsjail command line options (arguments before '--').

    Execution mode is fixed to ONCE (-Mo), mode parameter is not exposed.
    """

    # Filesystem
    chroot: str | None = None  # -c, --chroot DIR
    cwd: str | None = None  # --cwd DIR
    mounts: list[tuple[str, str, Literal["ro", "rw"]]] | None = None
    # -R, --bindmount_ro / -B, --bindmount (src, dst, mode)
    tmpfs: list[str] | None = None  # -T, --tmpfsmount DST

    # User/Group
    user: str | int | None = None  # -u, --user UID
    group: str | int | None = None  # -g, --group GID

    # Environment
    clear_env: bool | None = None  # None=don't pass, True=--keep_env=false
    env: dict[str, str] | None = None  # None/empty=don't pass, else --env k=v

    # Resource limits
    time_limit: int | None = None  # -t, --time_limit SEC (wall time)
    cpu_time_limit: int | None = None  # --rlimit_cpu SEC (CPU time)
    memory_limit: int | None = None  # --rlimit_as MB
    max_cpus: int | None = None  # --max_cpus N
    max_pids: int | None = None  # --cgroup_pids_max N
    max_open_files: int | None = None  # --rlimit_nofile N

    # Namespace control
    disable_clone_newnet: bool | None = None  # -N
    disable_clone_newuser: bool | None = None
    disable_clone_newpid: bool | None = None

    # Config file
    config_file: str | None = None  # -C, --config FILE

    def build_args(self) -> list[str]:
        """Build nsjail command line argument list.

        Rules:
        - None values don't generate arguments
        - Empty containers ({}, []) don't generate arguments
        - Other values (including "", 0, False) generate corresponding arguments
        - Always adds -Mo (ONCE mode)
        """
        args: list[str] = []

        # Always use ONCE mode
        args.append("-Mo")

        # Config file (applied first, overrides work)
        if self.config_file is not None:
            args.extend(["-C", self.config_file])

        # Filesystem
        if self.chroot is not None:
            args.extend(["-c", self.chroot])
        if self.cwd is not None:
            args.extend(["--cwd", self.cwd])
        if self.mounts:
            for src, dst, mode in self.mounts:
                if dst == src:
                    path = src
                else:
                    path = f"{src}:{dst}"
                if mode == "ro":
                    args.extend(["-R", path])
                else:  # rw
                    args.extend(["-B", path])
        if self.tmpfs:
            for dst in self.tmpfs:
                args.extend(["-T", dst])

        # User/Group
        if self.user is not None:
            args.extend(["-u", str(self.user)])
        if self.group is not None:
            args.extend(["-g", str(self.group)])

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
            args.extend(["-t", str(self.time_limit)])
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
            args.append("-N")
        if self.disable_clone_newuser:
            args.append("--disable_clone_newuser")
        if self.disable_clone_newpid:
            args.append("--disable_clone_newpid")

        return args
