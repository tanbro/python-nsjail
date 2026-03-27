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
    keep_env: bool | None = None  # None=don't pass, True=--keep_env=true
    env: Mapping[str, str] | None = None  # None/empty=don't pass, else --env k=v

    # Resource limits
    time_limit: int | None = None  # --time_limit SEC (wall time)
    rlimit_cpu: int | None = None  # --rlimit_cpu SEC (CPU time)
    rlimit_as: int | None = None  # --rlimit_as MB
    max_cpus: int | None = None  # --max_cpus N
    cgroup_pids_max: int | None = None  # --cgroup_pids_max N
    rlimit_nofile: int | None = None  # --rlimit_nofile N

    # Namespace control
    disable_clone_newnet: bool | None = None
    disable_clone_newuser: bool | None = None
    disable_clone_newpid: bool | None = None
    disable_clone_newipc: bool | None = None
    disable_clone_newuts: bool | None = None
    disable_clone_newcgroup: bool | None = None

    # UID/GID mapping (for unprivileged user namespaces)
    uid_mapping: str | None = None  # --uid_mapping "inside_uid:outside_uid:count"
    gid_mapping: str | None = None  # --gid_mapping "inside_gid:outside_gid:count"

    # Logging
    log_file: str | None = None  # --log PATH
    log_fd: int | None = None  # --log_fd FD
    verbose: bool | None = None  # --verbose
    quiet: bool | None = None  # --quiet
    really_quiet: bool | None = None  # --really_quiet

    # Capabilities
    keep_caps: bool | None = None  # --keep_caps
    cap: Sequence[str] | None = None  # --cap CAPABILITY

    # Seccomp
    seccomp_log: bool | None = None  # --seccomp_log
    seccomp_policy: str | None = None  # --seccomp_policy PATH

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
        if self.keep_env is not None:
            if self.keep_env:
                args.append("--keep_env=true")
            else:
                args.append("--keep_env=false")
        if self.env:
            for k, v in self.env.items():
                args.extend(["--env", f"{k}={v}"])

        # Resource limits
        if self.time_limit is not None:
            args.extend(["--time_limit", str(self.time_limit)])
        if self.rlimit_cpu is not None:
            args.extend(["--rlimit_cpu", str(self.rlimit_cpu)])
        if self.rlimit_as is not None:
            args.extend(["--rlimit_as", str(self.rlimit_as)])
        if self.max_cpus is not None:
            args.extend(["--max_cpus", str(self.max_cpus)])
        if self.cgroup_pids_max is not None:
            args.extend(["--cgroup_pids_max", str(self.cgroup_pids_max)])
        if self.rlimit_nofile is not None:
            args.extend(["--rlimit_nofile", str(self.rlimit_nofile)])

        # Namespace control
        if self.disable_clone_newnet:
            args.append("--disable_clone_newnet")
        if self.disable_clone_newuser:
            args.append("--disable_clone_newuser")
        if self.disable_clone_newpid:
            args.append("--disable_clone_newpid")
        if self.disable_clone_newipc:
            args.append("--disable_clone_newipc")
        if self.disable_clone_newuts:
            args.append("--disable_clone_newuts")
        if self.disable_clone_newcgroup:
            args.append("--disable_clone_newcgroup")

        # UID/GID mapping
        if self.uid_mapping is not None:
            args.extend(["--uid_mapping", self.uid_mapping])
        if self.gid_mapping is not None:
            args.extend(["--gid_mapping", self.gid_mapping])

        # Logging
        if self.log_file is not None:
            args.extend(["--log", self.log_file])
        if self.log_fd is not None:
            args.extend(["--log_fd", str(self.log_fd)])
        if self.verbose:
            args.append("--verbose")
        if self.quiet:
            args.append("--quiet")
        if self.really_quiet:
            args.append("--really_quiet")

        # Capabilities
        if self.keep_caps:
            args.append("--keep_caps")
        if self.cap:
            for c in self.cap:
                args.extend(["--cap", c])

        # Seccomp
        if self.seccomp_log:
            args.append("--seccomp_log")
        if self.seccomp_policy is not None:
            args.extend(["--seccomp_policy", self.seccomp_policy])

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
