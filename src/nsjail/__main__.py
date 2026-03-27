import os
import sys

from .locator import bundled_nsjail


def main():
    """Entry point for nsjail command.

    This function uses os.execl() to replace the current Python process
    with the nsjail binary, preserving the PID.
    """
    try:
        nsjail_bin = bundled_nsjail()
        os.execl(nsjail_bin, nsjail_bin, *sys.argv[1:])
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Run 'uv build --wheel' first if developing.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
