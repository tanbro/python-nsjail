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

    STANDALONE_ONCE = "o"
    """MODE_STANDALONE_ONCE: Launch with clone/execve, parent monitors child (default)."""

    STANDALONE_EXECVE = "e"
    """MODE_STANDALONE_EXECVE: Direct execve, no parent process (limits not enforced)."""

    STANDALONE_RERUN = "r"
    """MODE_STANDALONE_RERUN: Like ONCE but restart forever."""

    LISTEN_TCP = "l"
    """MODE_LISTEN_TCP: TCP listen mode, requires --port."""


@dataclass
class NsjailOptions(ProcessOptionsProtocol):
    """nsjail command line options (arguments before '--')."""

    # ==================== Execution Mode ====================
    mode: NsjailMode | str | None = None  # --mode|-M

    # ==================== Filesystem ====================
    chroot: str | None = None  # --chroot DIR
    cwd: str | None = None  # --cwd DIR
    hostname: str | None = None  # --hostname HOSTNAME
    proc_path: str | None = None  # --proc_path PATH
    proc_rw: bool | None = None  # --proc_rw (mount proc rw)
    rw: bool | None = None  # --rw (mount chroot as rw)
    no_pivotroot: bool | None = None  # --no_pivotroot

    # Mounts
    bindmount_ro: Sequence[str] | None = None  # --bindmount_ro|-R (read-only)
    bindmount: Sequence[str] | None = None  # --bindmount|-B (read-write)
    mount: Sequence[str] | None = None  # --mount|-m SRC:DST:FS_TYPE:OPTIONS
    symlink: Sequence[str] | None = None  # --symlink|-s SRC:DST
    tmpfsmount: Sequence[str] | None = None  # --tmpfsmount|-T DST

    # ==================== User/Group ====================
    user: str | int | None = None  # --user|-u UID
    group: str | int | None = None  # --group|-g GID
    uid_mapping: str | None = None  # --uid_mapping|-U "inside:outside:count"
    gid_mapping: str | None = None  # --gid_mapping|-G "inside:outside:count"

    # ==================== Environment ====================
    keep_env: bool | None = None  # --keep_env|-e (true/false)
    env: Mapping[str, str] | None = None  # --env|-E K=V

    # ==================== Resource Limits (rlimit) ====================
    time_limit: int | None = None  # --time_limit|-t SEC (wall time)
    rlimit_cpu: int | None = None  # --rlimit_cpu SEC (CPU time)
    rlimit_as: int | None = None  # --rlimit_as BYTES (address space)
    rlimit_core: int | None = None  # --rlimit_core BYTES (core dump)
    rlimit_fsize: int | None = None  # --rlimit_fsize BYTES (file size)
    rlimit_nproc: int | None = None  # --rlimit_nproc N (process count)
    rlimit_stack: int | None = None  # --rlimit_stack BYTES (stack)
    rlimit_memlock: int | None = None  # --rlimit_memlock BYTES (locked memory)
    rlimit_msgqueue: int | None = None  # --rlimit_msgqueue BYTES (POSIX msg queue)
    rlimit_nofile: int | None = None  # --rlimit_nofile N (open files)
    rlimit_rtprio: int | None = None  # --rlimit_rtprio PRIO (realtime priority)
    nice_level: int | None = None  # --nice_level N
    max_cpus: int | None = None  # --max_cpus N
    disable_rlimits: bool | None = None  # --disable_rlimits

    # ==================== cgroup v1 ====================
    # Memory
    cgroup_mem_max: int | None = None  # --cgroup_mem_max BYTES
    cgroup_mem_memsw_max: int | None = None  # --cgroup_mem_memsw_max BYTES
    cgroup_mem_swap_max: int | None = None  # --cgroup_mem_swap_max BYTES
    cgroup_mem_mount: str | None = None  # --cgroup_mem_mount PATH
    cgroup_mem_parent: str | None = None  # --cgroup_mem_parent NAME
    # PIDs
    cgroup_pids_max: int | None = None  # --cgroup_pids_max N
    cgroup_pids_mount: str | None = None  # --cgroup_pids_mount PATH
    cgroup_pids_parent: str | None = None  # --cgroup_pids_parent NAME
    # CPU
    cgroup_cpu_ms_per_sec: int | None = None  # --cgroup_cpu_ms_per_sec MSEC
    cgroup_cpu_mount: str | None = None  # --cgroup_cpu_mount PATH
    cgroup_cpu_parent: str | None = None  # --cgroup_cpu_parent NAME
    # Network class
    cgroup_net_cls_classid: int | None = None  # --cgroup_net_cls_classid ID
    cgroup_net_cls_mount: str | None = None  # --cgroup_net_cls_mount PATH
    cgroup_net_cls_parent: str | None = None  # --cgroup_net_cls_parent NAME

    # ==================== cgroup v2 ====================
    cgroupv2_mount: str | None = None  # --cgroupv2_mount PATH
    use_cgroupv2: bool | None = None  # --use_cgroupv2
    detect_cgroupv2: bool | None = None  # --detect_cgroupv2

    # ==================== Namespaces ====================
    disable_clone_newnet: bool | None = None  # --disable_clone_newnet|-N
    disable_clone_newuser: bool | None = None
    disable_clone_newns: bool | None = None  # --disable_clone_newns
    disable_clone_newpid: bool | None = None
    disable_clone_newipc: bool | None = None
    disable_clone_newuts: bool | None = None
    disable_clone_newcgroup: bool | None = None
    enable_clone_newtime: bool | None = None  # --enable_clone_newtime
    disable_no_new_privs: bool | None = None  # --disable_no_new_privs
    disable_proc: bool | None = None  # --disable_proc
    disable_tsc: bool | None = None  # --disable_tsc

    # ==================== Networking ====================
    iface_no_lo: bool | None = None  # --iface_no_lo
    iface_own: Sequence[str] | None = None  # --iface_own IFACE
    macvlan_iface: str | None = None  # --macvlan_iface|-I IFACE
    macvlan_vs_ip: str | None = None  # --macvlan_vs_ip IP
    macvlan_vs_nm: str | None = None  # --macvlan_vs_nm NETMASK
    macvlan_vs_gw: str | None = None  # --macvlan_vs_gw GATEWAY
    macvlan_vs_ma: str | None = None  # --macvlan_vs_ma MAC_ADDRESS
    macvlan_vs_mo: str | None = None  # --macvlan_vs_mo MTU
    use_pasta: bool | None = None  # --use_pasta

    # ==================== LISTEN Mode ====================
    port: int | None = None  # --port|-p PORT
    bindhost: str | None = None  # --bindhost HOST
    max_conns: int | None = None  # --max_conns N
    max_conns_per_ip: int | None = None  # --max_conns_per_ip|-i N

    # ==================== Execution ====================
    exec_file: str | None = None  # --exec_file|-x PATH
    execute_fd: bool | None = None  # --execute_fd

    # ==================== Logging ====================
    log_file: str | None = None  # --log|-l PATH
    log_fd: int | None = None  # --log_fd|-L FD
    verbose: bool | None = None  # --verbose|-v
    quiet: bool | None = None  # --quiet|-q
    really_quiet: bool | None = None  # --really_quiet|-Q
    silent: bool | None = None  # --silent
    stderr_to_null: bool | None = None  # --stderr_to_null

    # ==================== Process Control ====================
    daemon: bool | None = None  # --daemon|-d
    skip_setsid: bool | None = None  # --skip_setsid
    forward_signals: bool | None = None  # --forward_signals
    pass_fd: Sequence[int] | None = None  # --pass_fd FD

    # ==================== Capabilities ====================
    keep_caps: bool | None = None  # --keep_caps
    cap: Sequence[str] | None = None  # --cap CAPABILITY

    # ==================== Seccomp ====================
    seccomp_log: bool | None = None  # --seccomp_log
    seccomp_policy: str | None = None  # --seccomp_policy|-P PATH
    seccomp_string: str | None = None  # --seccomp_string STRING

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
        if self.proc_path is not None:
            args.extend(["--proc_path", self.proc_path])
        if self.proc_rw:
            args.append("--proc_rw")
        if self.rw:
            args.append("--rw")
        if self.no_pivotroot:
            args.append("--no_pivotroot")

        # Bind mounts
        if self.bindmount_ro:
            for bind in self.bindmount_ro:
                args.extend(["--bindmount_ro", bind])
        if self.bindmount:
            for bind in self.bindmount:
                args.extend(["--bindmount", bind])

        # Mounts and symlinks
        if self.mount:
            for m in self.mount:
                args.extend(["--mount", m])
        if self.symlink:
            for s in self.symlink:
                args.extend(["--symlink", s])

        # Tmpfs mounts
        if self.tmpfsmount:
            for dst in self.tmpfsmount:
                args.extend(["--tmpfsmount", dst])

        # User/Group
        if self.user is not None:
            args.extend(["--user", str(self.user)])
        if self.group is not None:
            args.extend(["--group", str(self.group)])
        if self.uid_mapping is not None:
            args.extend(["--uid_mapping", self.uid_mapping])
        if self.gid_mapping is not None:
            args.extend(["--gid_mapping", self.gid_mapping])

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
        if self.rlimit_core is not None:
            args.extend(["--rlimit_core", str(self.rlimit_core)])
        if self.rlimit_fsize is not None:
            args.extend(["--rlimit_fsize", str(self.rlimit_fsize)])
        if self.rlimit_nproc is not None:
            args.extend(["--rlimit_nproc", str(self.rlimit_nproc)])
        if self.rlimit_stack is not None:
            args.extend(["--rlimit_stack", str(self.rlimit_stack)])
        if self.rlimit_memlock is not None:
            args.extend(["--rlimit_memlock", str(self.rlimit_memlock)])
        if self.rlimit_msgqueue is not None:
            args.extend(["--rlimit_msgqueue", str(self.rlimit_msgqueue)])
        if self.rlimit_rtprio is not None:
            args.extend(["--rlimit_rtprio", str(self.rlimit_rtprio)])
        if self.max_cpus is not None:
            args.extend(["--max_cpus", str(self.max_cpus)])
        if self.rlimit_nofile is not None:
            args.extend(["--rlimit_nofile", str(self.rlimit_nofile)])
        if self.nice_level is not None:
            args.extend(["--nice_level", str(self.nice_level)])
        if self.disable_rlimits:
            args.append("--disable_rlimits")

        # cgroup v1: Memory
        if self.cgroup_mem_max is not None:
            args.extend(["--cgroup_mem_max", str(self.cgroup_mem_max)])
        if self.cgroup_mem_memsw_max is not None:
            args.extend(["--cgroup_mem_memsw_max", str(self.cgroup_mem_memsw_max)])
        if self.cgroup_mem_swap_max is not None:
            args.extend(["--cgroup_mem_swap_max", str(self.cgroup_mem_swap_max)])
        if self.cgroup_mem_mount is not None:
            args.extend(["--cgroup_mem_mount", self.cgroup_mem_mount])
        if self.cgroup_mem_parent is not None:
            args.extend(["--cgroup_mem_parent", self.cgroup_mem_parent])
        # cgroup v1: PIDs
        if self.cgroup_pids_max is not None:
            args.extend(["--cgroup_pids_max", str(self.cgroup_pids_max)])
        if self.cgroup_pids_mount is not None:
            args.extend(["--cgroup_pids_mount", self.cgroup_pids_mount])
        if self.cgroup_pids_parent is not None:
            args.extend(["--cgroup_pids_parent", self.cgroup_pids_parent])
        # cgroup v1: CPU
        if self.cgroup_cpu_ms_per_sec is not None:
            args.extend(["--cgroup_cpu_ms_per_sec", str(self.cgroup_cpu_ms_per_sec)])
        if self.cgroup_cpu_mount is not None:
            args.extend(["--cgroup_cpu_mount", self.cgroup_cpu_mount])
        if self.cgroup_cpu_parent is not None:
            args.extend(["--cgroup_cpu_parent", self.cgroup_cpu_parent])
        # cgroup v1: Network class
        if self.cgroup_net_cls_classid is not None:
            args.extend(["--cgroup_net_cls_classid", str(self.cgroup_net_cls_classid)])
        if self.cgroup_net_cls_mount is not None:
            args.extend(["--cgroup_net_cls_mount", self.cgroup_net_cls_mount])
        if self.cgroup_net_cls_parent is not None:
            args.extend(["--cgroup_net_cls_parent", self.cgroup_net_cls_parent])

        # cgroup v2
        if self.cgroupv2_mount is not None:
            args.extend(["--cgroupv2_mount", self.cgroupv2_mount])
        if self.use_cgroupv2:
            args.append("--use_cgroupv2")
        if self.detect_cgroupv2:
            args.append("--detect_cgroupv2")

        # Namespaces
        if self.disable_clone_newnet:
            args.append("--disable_clone_newnet")
        if self.disable_clone_newuser:
            args.append("--disable_clone_newuser")
        if self.disable_clone_newns:
            args.append("--disable_clone_newns")
        if self.disable_clone_newpid:
            args.append("--disable_clone_newpid")
        if self.disable_clone_newipc:
            args.append("--disable_clone_newipc")
        if self.disable_clone_newuts:
            args.append("--disable_clone_newuts")
        if self.disable_clone_newcgroup:
            args.append("--disable_clone_newcgroup")
        if self.enable_clone_newtime:
            args.append("--enable_clone_newtime")
        if self.disable_no_new_privs:
            args.append("--disable_no_new_privs")
        if self.disable_proc:
            args.append("--disable_proc")
        if self.disable_tsc:
            args.append("--disable_tsc")

        # Networking
        if self.iface_no_lo:
            args.append("--iface_no_lo")
        if self.iface_own:
            for iface in self.iface_own:
                args.extend(["--iface_own", iface])
        if self.macvlan_iface is not None:
            args.extend(["--macvlan_iface", self.macvlan_iface])
        if self.macvlan_vs_ip is not None:
            args.extend(["--macvlan_vs_ip", self.macvlan_vs_ip])
        if self.macvlan_vs_nm is not None:
            args.extend(["--macvlan_vs_nm", self.macvlan_vs_nm])
        if self.macvlan_vs_gw is not None:
            args.extend(["--macvlan_vs_gw", self.macvlan_vs_gw])
        if self.macvlan_vs_ma is not None:
            args.extend(["--macvlan_vs_ma", self.macvlan_vs_ma])
        if self.macvlan_vs_mo is not None:
            args.extend(["--macvlan_vs_mo", self.macvlan_vs_mo])
        if self.use_pasta:
            args.append("--use_pasta")

        # LISTEN mode
        if self.port is not None:
            args.extend(["--port", str(self.port)])
        if self.bindhost is not None:
            args.extend(["--bindhost", self.bindhost])
        if self.max_conns is not None:
            args.extend(["--max_conns", str(self.max_conns)])
        if self.max_conns_per_ip is not None:
            args.extend(["--max_conns_per_ip", str(self.max_conns_per_ip)])

        # Execution
        if self.exec_file is not None:
            args.extend(["--exec_file", self.exec_file])
        if self.execute_fd:
            args.append("--execute_fd")

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
        if self.silent:
            args.append("--silent")
        if self.stderr_to_null:
            args.append("--stderr_to_null")

        # Process control
        if self.daemon:
            args.append("--daemon")
        if self.skip_setsid:
            args.append("--skip_setsid")
        if self.forward_signals:
            args.append("--forward_signals")
        if self.pass_fd:
            for fd in self.pass_fd:
                args.extend(["--pass_fd", str(fd)])

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
        if self.seccomp_string is not None:
            args.extend(["--seccomp_string", self.seccomp_string])

        return args


@dataclass
class NsenterOptions(ProcessOptionsProtocol):
    """nsenter command line options.

    nsenter is used to enter the namespaces of a target process and execute
    a command. These options control how the namespaces are entered.
    """

    # Namespace selection
    all_namespaces: bool | None = None  # --all|-a (enter all namespaces)

    # Working directory
    wd: str | None = None  # --wd|-w PATH
    wdns: str | None = None  # --wdns DIR (working directory in namespace)

    # Root filesystem
    root: str | None = None  # --root|-r DIR

    # User/Group
    user: str | None = None  # --user|-S USER
    group: str | None = None  # --setgid|-G GROUP
    user_parent: bool | None = None  # --user-parent (enter parent user namespace)

    # Credentials
    preserve_credentials: bool = False  # --preserve-credentials
    keep_caps: bool | None = None  # --keep-caps (retain capabilities)

    # Environment
    env: bool | None = None  # --env|-e (inherit from target)

    # Process control
    no_fork: bool | None = None  # --no-fork|-F
    join_cgroup: bool | None = None  # --join-cgroup|-c

    # SELinux
    follow_context: bool | None = None  # --follow-context|-Z

    def build_args(self) -> Sequence[str]:
        """Build nsenter command line argument list.

        Rules:
        - None values don't generate arguments
        - Empty containers ({}, []) don't generate arguments
        - Other values (including "", 0, False) generate corresponding arguments
        - Uses long format for all options
        """
        args: list[str] = []

        # Namespace selection
        if self.all_namespaces:
            args.append("--all")

        # Working directory
        if self.wd is not None:
            args.extend(["--wd", self.wd])
        if self.wdns is not None:
            args.extend(["--wdns", self.wdns])

        # Root filesystem
        if self.root is not None:
            args.extend(["--root", self.root])

        # User/Group
        if self.user is not None:
            args.extend(["--user", self.user])
        if self.group is not None:
            args.extend(["--setgid", self.group])
        if self.user_parent:
            args.append("--user-parent")

        # Credentials
        if self.preserve_credentials:
            args.append("--preserve-credentials")
        if self.keep_caps:
            args.append("--keep-caps")

        # Environment
        if self.env:
            args.append("--env")

        # Process control
        if self.no_fork:
            args.append("--no-fork")
        if self.join_cgroup:
            args.append("--join-cgroup")

        # SELinux
        if self.follow_context:
            args.append("--follow-context")

        return args
