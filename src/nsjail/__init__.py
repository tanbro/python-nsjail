"""nsjail binary distribution.

This package provides the nsjail binary executable.
"""

import shutil
import sysconfig
from pathlib import Path

__version__ = "1.0.0"
__nsjail_version__ = "3.6"


def status() -> dict[str, Path]:
    """Find all nsjail binaries and their status.

    Returns:
        dict: Keys are 'system', 'package', 'dev'. Only includes found binaries.
        Empty dict if no nsjail found.
    """
    result: dict[str, Path] = {}

    # in path
    if which_nsjail := shutil.which("nsjail"):
        result["system"] = Path(which_nsjail)

    # pip installed
    installed = Path(sysconfig.get_path("scripts")) / "nsjail"
    if installed.exists():
        result["package"] = installed

    # local development
    dev_binary = Path(__file__).parent.parent.parent / "nsjail" / "nsjail"
    if dev_binary.exists():
        result["dev"] = dev_binary

    return result


def main() -> None:
    """Entry point for nsjail-status command."""
    info = status()

    print("nsjail status:")
    print(f"  System:   {info.get('system', '(not found)')}")
    print(f"  Package:  {info.get('package', '(not found)')}")
    print(f"  Dev:      {info.get('dev', '(not found)')}")
    print()
    print(f"Package version: {__version__}")
    print(f"Bundled nsjail:  {__nsjail_version__}")


if __name__ == "__main__":
    main()
