"""Utilities for finding nsjail binary."""

from __future__ import annotations

import os.path
import shutil
import sysconfig
import warnings
import importlib.resources as resources
from pathlib import Path

from ._nsjail_version import __nsjail_version__
from .version import __version__

__all__ = ["get_nsjail_path", "bundled_binary", "console_script", "which_nsjail"]


def which_nsjail() -> str | None:
    """Get nsjail binary from system PATH (internal).

    Returns:
        Path to nsjail binary if found in PATH, None otherwise.
    """
    return shutil.which("nsjail")


def bundled_binary() -> Path:
    """Get path to the bundled nsjail binary in this package.

    The binary is installed as package data alongside this module.

    Returns:
        Path to bundled nsjail binary if it exists, None otherwise.
    """
    binary_path = resources.files(__package__) / "nsjail"
    if binary_path.is_file():
        return Path(str(binary_path)).resolve()
    raise FileNotFoundError("Can not find bundled nsjail executable file")


def console_script() -> Path | None:
    """Get path to our installed console script (e.g., venv/bin/nsjail).

    Returns:
        Path to the console script if found, None otherwise.
    """
    if scripts_dir := sysconfig.get_path("scripts"):
        script_path = Path(scripts_dir) / "nsjail"
        if script_path.is_file():
            return script_path.resolve()
    return None


def get_nsjail_path() -> Path:
    """Get the appropriate nsjail binary to use.

    Priority:
    1. NSJAIL environment variable (supports ~ and $VAR expansion)
    2. Bundled binary (always preferred, known version)
    3. System nsjail from PATH

    Returns:
        Path to nsjail binary.

    Raises:
        RuntimeError: If nsjail binary not found.
    """
    # Check NSJAIL environment variable first
    if env_path := os.environ.get("NSJAIL"):
        # Expand ~ and environment variables ($VAR, ${VAR})
        expanded = os.path.expandvars(os.path.expanduser(env_path))
        return Path(expanded).resolve()

    # Try bundled binary
    try:
        return bundled_binary()
    except FileNotFoundError as e:
        warnings.warn(str(e), ResourceWarning)

    # Check system PATH
    if which_ := which_nsjail():
        return Path(which_)

    raise RuntimeError("nsjail binary not found")


def main() -> None:
    """Entry point for nsjail-status command."""
    which_ = which_nsjail()
    bundled = bundled_binary()
    script = console_script()

    print("nsjail status:")
    print(f"  System PATH:   {which_ if which_ else '(not found)'}")
    print(f"  Bundled:       {bundled if bundled else '(not found)'}")
    print(f"  Script:       {script if script else '(not found)'}")
    print()
    print(f"Package version: {__version__}")
    print(f"Bundled nsjail:  {__nsjail_version__}")


if __name__ == "__main__":
    main()
