# python-nsjail

> Prebuilt [nsjail](https://github.com/google/nsjail) executables packaged as Python wheels

## Overview

`python-nsjail` provides prebuilt nsjail binaries as Python wheels, plus a **Python API** for programmatic sandboxing.

**Features**:
- Prebuilt nsjail binary for Linux (x86_64, aarch64)
- Async Python API for process isolation
- Chroot, user/group, resource limits, mount controls

## Installation

```bash
pip install python-nsjail
```

This creates an `nsjail` command in your environment's `bin/` directory (e.g., `~/.local/bin/nsjail` or `/some/where/.venv/bin/nsjail`).

**How it works**: The `nsjail` command is a small Python wrapper that executes the actual nsjail binary bundled inside the package. The wrapper uses `os.execl()` to replace itself with the real binary, preserving the process ID.

### Virtual Environment (Recommended)

Using a virtual environment keeps nsjail isolated:

```bash
# Create venv
python -m venv .venv
source .venv/bin/activate

# Install python-nsjail
pip install python-nsjail

# Verify
nsjail-status
```

## Usage

### Python API

```python
import asyncio
from nsjail import NsjailOptions, NsjailProcess, create_nsjail_process

async def main():
    # Basic usage
    proc = await create_nsjail_process(
        command="/bin/echo",
        args=["hello"],
        options=NsjailOptions(chroot="/"),
    )
    await proc.wait()

    # Stream output
    proc = await create_nsjail_process(
        command="/bin/cat",
        args=["/etc/hostname"],
        options=NsjailOptions(
            chroot="/",
            user="nobody",
            mounts=[("/etc/hostname", "/etc/hostname", "ro")],
        ),
    )
    async for source, chunk in proc.stream():
        if source == "stdout":
            print(chunk.decode())

asyncio.run(main())
```

### Command line

```bash
nsjail --help
```

```bash
nsjail-status
```

Output:
```
nsjail status:
  System PATH:   /usr/bin/nsjail
  Bundled:       /path/to/bundled/nsjail
  Script:        /path/to/wrapper/nsjail

Package version: 0.1.0
Bundled nsjail:  3.6
```

### Environment Variables

**`NSJAIL`** - Path to nsjail binary (overrides auto-detection)

Supports `~` and `$VAR` expansion:

```bash
# Use custom nsjail
export NSJAIL=/opt/nsjail/bin/nsjail

# With ~ expansion
export NSJAIL=~/local/bin/nsjail

# With environment variable expansion
export NSJAIL=$XDG_DATA_HOME/nsjail/bin/nsjail
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
