# python-nsjail

> nsjail binary distribution — Prebuilt static nsjail executables packaged as Python Wheels

## Overview

`python-nsjail` is not a Python library. It's a **binary distribution tool** that packages prebuilt static [nsjail](https://github.com/google/nsjail) executables as Python Wheels for easy installation via `pip`.

### Design Goals

- **Zero dependencies**: Contains no Python runtime code, only distributes binaries
- **Statically linked**: nsjail binaries are independent of glibc/libc, run on any Linux distro
- **Multi-architecture**: Supports x86_64, aarch64, and more
- **Auto-selection**: pip automatically selects the matching architecture

## Installation

```bash
pip install nsjail
```

After installation, the nsjail binary is placed at:

```
/opt/nsjail/bin/nsjail
```

## Usage

### Direct invocation

```python
import subprocess
import shutil

nsjail_path = shutil.which("nsjail")  # /opt/nsjail/bin/nsjail
subprocess.run([nsjail_path, "--help"])
```

### As a dependency

Other Python projects can depend on this package to get the nsjail binary:

```toml
# pyproject.toml
[project]
dependencies = ["nsjail>=0.1.0"]
```

```python
import shutil

nsjail_path = shutil.which("nsjail")
if not nsjail_path:
    raise RuntimeError("nsjail not found")

# Use nsjail...
```

## Distribution

Each architecture gets its own wheel:

```
nsjail-0.1.0-py3-none-linux_x86_64.whl   # ~1.5 MB
nsjail-0.1.0-py3-none-linux_aarch64.whl  # ~1.4 MB
```

pip automatically selects the wheel matching your architecture.

## System Requirements

- **OS**: Linux (kernel 3.10+)
- **Python**: 3.10+ (only for installation; no Python code is executed)
- **Permissions**: Using nsjail requires CAP_SYS_ADMIN or root

## Building

See [CONTRIBUTING.md](CONTRIBUTING.md) for building multi-architecture wheels.

## License

- **nsjail**: Apache 2.0 (see [nsjail/LICENSE](https://github.com/google/nsjail))
- **packaging**: MIT

## Related Projects

- [google/nsjail](https://github.com/google/nsjail) - Upstream nsjail project
- [jailer](https://github.com/yourorg/jailer) - Python sandbox wrapper built on nsjail
