# python-nsjail

> Prebuilt [nsjail](https://github.com/google/nsjail) executables packaged as Python wheels

## Overview

`python-nsjail` distributes the nsjail binary as a Python package for easy installation via `pip`.

**Note**: This is not a Python library — it only provides the nsjail binary executable.

## Installation

```bash
pip install nsjail
```

This creates an `nsjail` command in your environment's `bin/` directory (e.g., `~/.local/bin/nsjail` or `venv/bin/nsjail`).

**How it works**: The `nsjail` command is a small Python wrapper that executes the actual nsjail binary bundled inside the package. The wrapper uses `os.execl()` to replace itself with the real binary, preserving the process ID.

### Virtual Environment (Recommended)

Using a virtual environment keeps nsjail isolated:

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate

# Install nsjail
pip install nsjail

# Verify
nsjail-status
```

## Usage

### Command line

```bash
nsjail --help
```

### Check nsjail path

```bash
nsjail-find
```

Output:
```
nsjail status:
  System PATH:   /root/workspaces/python-nsjail/.venv/bin/nsjail
  Bundled:       /root/workspaces/python-nsjail/src/nsjail/nsjail

Package version: 0.1.0b3.dev1+g71c0da62d.d20260323
Bundled nsjail:  3.6
```

## Building from Source

For development or building from source, see [CONTRIBUTING.md](CONTRIBUTING.md).

## System Requirements

- **OS**: **Linux only**
- **Kernel**: **Linux 5.10+** (some nsjail features require newer kernel syscalls)
- **Permissions**: Using nsjail requires CAP_SYS_ADMIN or root
- **Python**: Python 3.9+

### Platform Compatibility

| Platform | libc | Compatible With | CPU Requirement |
|----------|------|-----------------|-----------------|
| manylinux_2_34_x86_64 | glibc 2.34 | Ubuntu 22.04+, Debian 12+, RHEL 9+ | x86-64-v2* (SSE4.2, POPCNT) |
| manylinux_2_34_aarch64 | glibc 2.34 | ARM64 systems | ARM64 (v8+) |
| musllinux_1_2_x86_64 | musl 1.2 | Alpine Linux, other musl-based | x86-64-v2* (SSE4.2, POPCNT) |
| musllinux_1_2_aarch64 | musl 1.2 | Alpine Linux ARM64 | ARM64 (v8+) |

> ⚠️ **`x86-64-v2` Note**: \
> The x86_64 wheels are built with `manylinux_2_34` containers which use `x86-64-v2` by default. This requires a CPU from ~2010 or later (supports SSE4.2 and POPCNT instructions). Most modern systems support this.
> If you need to run on older x86-64 hardware (pre-2010), please use the source distribution or build from source.

## License

- **nsjail**: Apache-2.0 (see [google/nsjail](https://github.com/google/nsjail))
- **python-nsjail packaging**: Apache-2.0
