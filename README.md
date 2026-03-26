# python-nsjail

> Prebuilt [nsjail](https://github.com/google/nsjail) executables packaged as Python wheels with a simple Python API

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

## Python API

The library provides simple functions for creating nsjail subprocesses. Both synchronous and asynchronous APIs are available.

### Basic Usage

**Async API**:

```python
import asyncio
import subprocess
from nsjail import async_create_nsjail, NsjailOptions

async def main():
    # Basic usage - output to terminal
    proc = await async_create_nsjail(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )
    await proc.wait()

    # Capture output
    proc = await async_create_nsjail(
        command=["/bin/cat", "/etc/hostname"],
        options=NsjailOptions(chroot="/", user="nobody"),
        stdout=subprocess.PIPE,
    )
    output = await proc.stdout.read()
    print(output.decode())

asyncio.run(main())
```

**Sync API**:

```python
import subprocess
from nsjail import create_nsjail, NsjailOptions

# Capture output synchronously
proc = create_nsjail(
    command=["/bin/echo", "hello"],
    options=NsjailOptions(chroot="/"),
    stdout=subprocess.PIPE,
)
output, _ = proc.communicate()
print(output.decode())
```

### Stream Merging

For processes that output to both stdout and stderr, use `merge_streams`:

```python
import asyncio
import subprocess
from nsjail import async_create_nsjail, merge_streams, NsjailOptions

async def main():
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "echo out; echo err >&2"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    async for source, chunk in merge_streams(proc):
        if source == "stdout":
            print(f"stdout: {chunk.decode()}")
        else:
            print(f"stderr: {chunk.decode()}", file=sys.stderr)

asyncio.run(main())
```

### Using nsenter

Enter an existing container's namespace with `async_create_nsenter`:

```python
import asyncio
import subprocess
from nsjail import async_create_nsenter

async def main():
    # Run 'ip addr' inside container 1234's network namespace
    proc = await async_create_nsenter(
        target_pid=1234,
        namespaces=["net"],
        command=["ip", "addr"],
        stdout=subprocess.PIPE,
    )
    output = await proc.stdout.read()
    print(output.decode())

asyncio.run(main())
```

### Inspect Command Arguments

For debugging or testing, you can build the nsjail arguments without executing:

```python
from nsjail import build_nsjail_args, NsjailOptions

args = build_nsjail_args(
    options=NsjailOptions(chroot="/", user="nobody"),
    config_file="/path/to/config.cfg",
)
print("nsjail", *args, "--", "/bin/echo", "hello")
# Output: nsjail --chroot / --user nobody --config /path/to/config.cfg -- /bin/echo hello
```

### Passing Additional Arguments

All `*args` and `**kwargs` are passed directly to the underlying subprocess creation functions:

```python
import subprocess
from nsjail import async_create_nsjail, NsjailOptions

# Pass cwd, env, and other subprocess.Popen / asyncio.create_subprocess_exec arguments
proc = await async_create_nsjail(
    command=["/bin/sh", "-c", "echo $FOO"],
    options=NsjailOptions(chroot="/"),
    stdout=subprocess.PIPE,
    cwd="/tmp",
    env={"FOO": "value"},
)
```

### NsjailOptions

Configure nsjail with `NsjailOptions`:

```python
from nsjail import NsjailOptions

options = NsjailOptions(
    chroot="/srv/jail",           # Chroot directory
    user=65534,                    # Run as user (UID)
    group=65534,                   # Run as group (GID)
    hostname="sandbox",            # Set hostname
    cwd="/tmp",                    # Working directory inside jail
    env={"HOME": "/tmp"},          # Environment variables
    bindmount=["/tmp:/tmp"],       # Read-write bind mounts
    bindmount_ro=["/lib:/lib"],    # Read-only bind mounts
    tmpfsmount=["/tmp"],           # Temporary filesystem mounts
    time_limit=60,                 # Wall time limit in seconds
    memory_limit=512,              # Memory limit in MB
    # ... see NsjailOptions for all options
)
```

### Environment Variable

`NSJAIL` - Override the nsjail binary path (for Python API only)

```bash
export NSJAIL=/custom/path/to/nsjail
```

Supports `~` and `$VAR` expansion:
```bash
export NSJAIL=~/local/bin/nsjail
export NSJAIL=$XDG_DATA_HOME/nsjail/bin/nsjail
```

## API Reference

### Async Functions

- `async_create_nsjail(command, options=None, config_file=None, *args, **kwargs)` - Create async nsjail subprocess
- `async_create_nsenter(target_pid, namespaces, command, options=None, *args, **kwargs)` - Create async nsenter subprocess
- `merge_streams(proc, chunk_size=8192, stdout=True, stderr=True)` - Merge stdout/stderr streams

### Sync Functions

- `create_nsjail(command, options=None, config_file=None, *args, **kwargs)` - Create sync nsjail subprocess
- `create_nsenter(target_pid, namespaces, command, options=None, *args, **kwargs)` - Create sync nsenter subprocess

### Helper Functions

- `build_nsjail_args(options=None, config_file=None)` - Build nsjail command-line arguments
- `build_nsenter_args(target_pid, namespaces, options=None)` - Build nsenter command-line arguments

### Classes

- `NsjailOptions` - nsjail configuration options
- `NsenterOptions` - nsenter configuration options

### Locator Functions

- `locate_nsjail()` - Find nsjail binary (respects NSJAIL env var)
- `bundled_binary()` - Get bundled nsjail binary path

## Building from Source

For development or building from source, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

- **nsjail**: Apache-2.0 (see [google/nsjail](https://github.com/google/nsjail))
- **python-nsjail packaging**: Apache-2.0

[nsjail]: https://github.com/google/nsjail "A lightweight process isolation tool that utilizes Linux namespaces, cgroups, rlimits and seccomp-bpf syscall filters, leveraging the Kafel BPF language for enhanced security."
