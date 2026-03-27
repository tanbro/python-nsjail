import os
import sys

from .locator import bundled_nsjail


def main():
    """Entry point for nsjail command.

    This function uses os.execl() to replace the current Python process
    with the nsjail binary, preserving the PID.
    """
    # Find the nsjail binary relative to this module
    nsjail_bin = bundled_nsjail()

    # Replace current process with nsjail (preserves PID)
    # os.execl() replaces the current process image with a new one
    # The PID remains the same, which is important for nsjail's use case
    os.execl(nsjail_bin, nsjail_bin, *sys.argv[1:])


if __name__ == "__main__":
    main()
