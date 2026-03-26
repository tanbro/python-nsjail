"""Utilities for locating nsjail binary."""

from __future__ import annotations

import os.path
import shutil
import sysconfig
import warnings
import importlib.resources as resources
from pathlib import Path

__all__ = ("locate_nsjail", "bundled_nsjail", "which_nsjail", "scripts_nsjail")


def which_nsjail() -> str | None:
    """Get nsjail binary from system PATH (internal).

    Returns:
        Path to nsjail binary if found in PATH, None otherwise.
    """
    return shutil.which("nsjail")


def bundled_nsjail() -> Path:
    """Get path to the bundled nsjail binary in this package.

    The binary is installed as package data alongside this module.

    Returns:
        Path to bundled nsjail binary if it exists, None otherwise.
    """
    binary_path = resources.files(__package__) / "nsjail"
    if binary_path.is_file():
        return Path(str(binary_path)).resolve()
    raise FileNotFoundError("Can not find bundled nsjail executable file")


def scripts_nsjail() -> Path | None:
    """Get path to our installed console script (e.g., venv/bin/nsjail).

    Returns:
        Path to the console script if found, None otherwise.
    """
    if scripts_dir := sysconfig.get_path("scripts"):
        script_path = Path(scripts_dir) / "nsjail"
        if script_path.is_file():
            return script_path.resolve()
    return None


def locate_nsjail() -> Path:
    """Locate the appropriate nsjail binary to use.

    Priority:
    1. NSJAIL environment variable (supports ~ and $VAR expansion)
    2. System nsjail from common locations (/usr/local/bin, /usr/bin)
    3. Bundled binary (fallback)

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

    # Check common system paths
    for path in ("/usr/local/bin", "/usr/bin"):
        nsjail_path = Path(path) / "nsjail"
        if nsjail_path.is_file():
            return nsjail_path.resolve()

    # Try bundled binary as fallback
    try:
        return bundled_nsjail()
    except FileNotFoundError as e:
        warnings.warn(str(e), ResourceWarning)

    raise RuntimeError("nsjail binary not found")
