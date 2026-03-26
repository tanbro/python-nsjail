"""Synchronous subprocess creation for nsjail and nsenter.

This module provides simple functions for creating nsjail and nsenter
subprocesses without wrapper classes.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath

from .locator import locate_nsjail
from .options import NsenterOptions, NsjailOptions
from .types import NamespaceType, NS_FLAGS

__all__ = ("create_nsjail", "create_nsenter", "build_nsjail_args", "build_nsenter_args")


# ==================== Public Helper Functions ====================


def build_nsjail_args(
    options: NsjailOptions | None = None,
    config: StrPath | None = None,
) -> list[str]:
    """Build nsjail command line arguments.

    For debugging, testing, or manual execution.

    Args:
        options: NsjailOptions configuration
        config: Path to nsjail config file

    Returns:
        List of nsjail command line arguments (without binary path and command)

    Example:
        >>> args = build_nsjail_args(NsjailOptions(chroot="/"))
        >>> print(args)
        ['--chroot', '/']
    """
    args: list[str] = []
    if config is not None:
        args.extend(["--config", str(config)])
    if options is not None:
        args.extend(options.build_args())
    return args


def build_nsenter_args(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    options: NsenterOptions | None = None,
) -> list[str]:
    """Build nsenter command line arguments.

    For debugging, testing, or manual execution.

    Args:
        target_pid: Target process PID
        namespaces: List of namespace types to enter
        options: NsenterOptions configuration

    Returns:
        List of nsenter command line arguments (without binary path and command)

    Example:
        >>> args = build_nsenter_args(1234, ["net"])
        >>> print(args)
        ['--target', '1234', '-n']
    """
    args = ["--target", str(target_pid)]

    ns_flags = set()
    for ns in namespaces:
        try:
            flag = NS_FLAGS[ns]
        except KeyError as exc:
            raise ValueError(f"Unknown namespace type: {exc}")
        ns_flags.add(flag)
    args.extend(ns_flags)

    if options is not None:
        args.extend(options.build_args())

    return args


# ==================== Factory Functions ====================


def create_nsjail(
    command: Sequence[str],
    options: NsjailOptions | None = None,
    config: StrPath | None = None,
    *args,
    **kwargs,
) -> subprocess.Popen:
    """Create nsjail subprocess (synchronous).

    Args:
        command: Command to execute inside nsjail
        options: NsjailOptions configuration
        config: Path to nsjail config file
        *args, **kwargs: Additional arguments passed to subprocess.Popen

    Returns:
        subprocess.Popen instance

    Example:
        >>> proc = create_nsjail(["/bin/echo", "hello"], stdout=subprocess.PIPE)
        >>> output, _ = proc.communicate()
    """
    nsjail_path = locate_nsjail()
    nsjail_args = build_nsjail_args(options, config)

    cmd: list[str] = [str(nsjail_path), *nsjail_args, "--", *command]
    return subprocess.Popen(cmd, *args, **kwargs)


def create_nsenter(
    target_pid: int,
    namespaces: Iterable[NamespaceType],
    command: Sequence[str],
    options: NsenterOptions | None = None,
    *args,
    **kwargs,
) -> subprocess.Popen:
    """Create nsenter subprocess (synchronous).

    Args:
        target_pid: Target process PID
        namespaces: List of namespace types to enter
        command: Command to execute inside the namespace
        options: NsenterOptions configuration
        *args, **kwargs: Additional arguments passed to subprocess.Popen

    Returns:
        subprocess.Popen instance

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
    cmd: list[str] = [nsenter_path, *nsenter_args, "--", *command]
    return subprocess.Popen(cmd, *args, **kwargs)
