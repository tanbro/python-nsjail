"""CLI entry point for nsjail-status command."""

from ._nsjail_version import __nsjail_version__
from .version import __version__
from .locator import which_nsjail, bundled_binary, console_script


def main() -> None:
    """Entry point for nsjail-status command."""
    which_ = which_nsjail()
    bundled = bundled_binary()
    script = console_script()

    print("nsjail status:")
    print(f"  System PATH:   {which_ if which_ else '(not found)'}")
    print(f"  Bundled:       {bundled if bundled else '(not found)'}")
    print(f"  Script:        {script if script else '(not found)'}")
    print()
    print(f"Package version: {__version__}")
    print(f"Bundled nsjail:  {__nsjail_version__}")


if __name__ == "__main__":
    main()
