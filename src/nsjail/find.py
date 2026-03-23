"""Utilities for finding nsjail binary."""

from __future__ import annotations

import importlib.resources as resources
import shutil
from pathlib import Path

from ._nsjail_version import __nsjail_version__
from .version import __version__

__all__ = ["find_system_nsjail", "find_bundled_nsjail"]


def find_system_nsjail() -> str | None:
    """Find nsjail binary in system PATH.

    Returns:
        Path to nsjail binary if found in PATH, None otherwise.
    """
    return shutil.which("nsjail")


def find_bundled_nsjail() -> Path | None:
    """Get path to the bundled nsjail binary in this package.

    The binary is installed as package_data alongside this module.

    Returns:
        Path to bundled nsjail binary if it exists, None otherwise.
    """
    pkg_dir = resources.files("nsjail")
    binary_path = pkg_dir / "nsjail"
    if binary_path.is_file():
        return Path(str(binary_path))
    return None


def main() -> None:
    """Entry point for nsjail-status command."""
    system = find_system_nsjail()
    bundled = find_bundled_nsjail()

    print("nsjail status:")
    print(f"  System PATH:   {system if system else '(not found)'}")
    print(f"  Bundled:       {bundled if bundled else '(not found)'}")
    print()
    print(f"Package version: {__version__}")
    print(f"Bundled nsjail:  {__nsjail_version__}")



if __name__ == "__main__":
    main()
