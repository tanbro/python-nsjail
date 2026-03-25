# python-nsjail

> Prebuilt [nsjail](https://github.com/google/nsjail) executables packaged as Python wheels

[![CI](https://github.com/tanbro/python-nsjail/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/tanbro/python-nsjail/actions/workflows/build-and-publish.yml)
[![GitHub tags](https://img.shields.io/github/v/tag/tanbro/python-nsjail)](https://github.com/tanbro/python-nsjail/tags)
[![PyPI version](https://badge.fury.io/py/python-nsjail.svg)](https://pypi.org/project/python-nsjail/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-nsjail)](https://pypi.org/project/python-nsjail/)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/python-nsjail)](https://pypi.org/project/python-nsjail/)
[![PyPI - Status](https://img.shields.io/pypi/status/python-nsjail)](https://pypi.org/project/python-nsjail/)
[![PyPI - License](https://img.shields.io/pypi/l/python-nsjail)](https://pypi.org/project/python-nsjail/)

## Overview

**Just install and use** — no compilation required. `python-nsjail` provides prebuilt [nsjail][] binaries as Python wheels, making the powerful Linux namespace sandbox immediately available.

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

## Installation

```bash
pip install python-nsjail
```

Now run:

```bash
nsjail --help
```

You got `nsjail` installed!

### Where is the nsjail binary?

The installation location depends on how you install:

**Virtual environment** (recommended):
```bash
python -m venv .venv
source .venv/bin/activate
pip install python-nsjail
# Binary: .venv/bin/nsjail
```

**User install**:
```bash
pip install --user python-nsjail
# Binary: ~/.local/bin/nsjail
```

**System install** (requires root):
```bash
pip install python-nsjail
# Binary: /usr/local/bin/nsjail
```

### Verify Installation

```bash
nsjail --help
```

and the status(in python environment's scripts directory):

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

### Getting the Binary Path from Python

If you need the nsjail binary path in your scripts:

```python
from nsjail import bundled_binary

nsjail_path = bundled_binary()
print(nsjail_path)  # /absolute/path/to/nsjail
```

Or use `locate_nsjail()` which respects the `NSJAIL` environment variable and checks system paths:

```python
from nsjail import locate_nsjail

nsjail_path = locate_nsjail()  # Returns path with priority: env var > system > bundled
```

Priority:
1. `NSJAIL` environment variable (if set)
2. System paths: `/usr/local/bin`, `/usr/bin`
3. Bundled binary (fallback)

```python
from nsjail import locate_nsjail

nsjail_path = locate_nsjail()
```

## Python API

For programmatic sandboxing, use the async Python API:

**Environment Variable** (for Python API only):

`NSJAIL` - Override the nsjail binary path

```bash
export NSJAIL=/custom/path/to/nsjail
```

Supports `~` and `$VAR` expansion:
```bash
export NSJAIL=~/local/bin/nsjail
export NSJAIL=$XDG_DATA_HOME/nsjail/bin/nsjail
```

```python
import asyncio
from nsjail import create_nsjail_process, create_nsenter_process, NsjailOptions

async def main():
    # Basic usage
    proc = await create_nsjail_process(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )
    await proc.wait()

    # Stream output
    proc = await create_nsjail_process(
        command=["/bin/cat", "/etc/hostname"],
        options=NsjailOptions(
            chroot="/",
            user="nobody",
            mounts=[("/etc/hostname", "/etc/hostname", "ro")],
        ),
    )
    async for source, chunk in proc.stream():
        if source == "stdout":
            print(chunk.decode())

    # Interactive stdin (with writable_stdin=True)
    proc = await create_nsjail_process(
        command=["/bin/cat"],
        options=NsjailOptions(chroot="/"),
        writable_stdin=True,
    )
    await proc.write(b"hello world\n")
    # ... read output via stream()

    # Use nsenter to enter existing container namespace
    nsenter_proc = await create_nsenter_process(
        target_pid=1234,
        namespaces=["net", "mnt"],
        command=["ip", "addr"],
    )

asyncio.run(main())
```

## Building from Source

For development or building from source, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

- **nsjail**: Apache-2.0 (see [google/nsjail](https://github.com/google/nsjail))
- **python-nsjail packaging**: Apache-2.0

[nsjail]: https://github.com/google/nsjail "A lightweight process isolation tool that utilizes Linux namespaces, cgroups, rlimits and seccomp-bpf syscall filters, leveraging the Kafel BPF language for enhanced security."
