import os
import sys
from pathlib import Path

def main()->None:
    """Entry point for nsjail command.

    This function uses os.execl() to replace the current Python process
    with the nsjail binary, preserving the PID.
    """
    # Find the nsjail binary relative to this module
    here = Path(__file__).parent.resolve()
    nsjail_bin = here / "nsjail"

    if not nsjail_bin.exists():
        print(f"Error: nsjail binary not found at {nsjail_bin}", file=sys.stderr)
        print("This package may not be installed correctly.", file=sys.stderr)
        sys.exit(-1)

    # Replace current process with nsjail (preserves PID)
    # os.execl() replaces the current process image with a new one
    # The PID remains the same, which is important for nsjail's use case
    try:
        os.execl(nsjail_bin, nsjail_bin, *sys.argv[1:])
    except OSError as e:
        print(f"Error executing nsjail: {e}", file=sys.stderr)
        sys.exit(-2)



if __name__ == "__main__":
    main()
