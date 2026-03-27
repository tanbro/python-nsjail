"""CLI entry point for nsjail-status command."""

import shutil

from ._nsjail_version import __nsjail_version__
from .version import __version__
from .locator import which_nsjail, bundled_nsjail, scripts_nsjail


def main() -> None:
    """Entry point for nsjail-status command."""
    which_ = which_nsjail()
    bundled = bundled_nsjail()
    script = scripts_nsjail()

    # nsenter status
    which_nsenter = shutil.which("nsenter")

    print("nsjail status:")
    print(f"  System PATH:   {which_ if which_ else '(not found)'}")
    print(f"  Bundled:       {bundled if bundled else '(not found)'}")
    print(f"  Script:        {script if script else '(not found)'}")
    print()
    print("nsenter status:")
    print(f"  Available:     {'yes' if which_nsenter else 'no (install util-linux)'}")
    print(f"  Path:          {which_nsenter if which_nsenter else '(not found)'}")
    print()
    print(f"Package version: {__version__}")
    print(f"Bundled nsjail:  {__nsjail_version__}")


if __name__ == "__main__":
    main()
