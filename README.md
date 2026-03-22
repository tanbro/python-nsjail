# python-nsjail

> Prebuilt [nsjail](https://github.com/google/nsjail) executables packaged as Python wheels

## Overview

`python-nsjail` distributes the nsjail binary as a Python package for easy installation via `pip`.

**Note**: This is not a Python library — it only provides the nsjail binary executable.

## Installation

```bash
pip install nsjail
```

The `nsjail` binary is installed to your environment's `bin/` directory (e.g., `~/.local/bin/nsjail` or `venv/bin/nsjail`).

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

### Check installation status

```bash
nsjail-status
```

Output:
```
nsjail status:
  System:   (not found)
  Package:  /venv/bin/nsjail ✓
  Dev:      (not found)

Package version: 1.0.0
Bundled nsjail:  3.6
```

### Python API

```python
import nsjail

# Get status of all nsjail binaries
info = nsjail.status()
# Returns: {'system': Path | None, 'package': Path | None, 'dev': Path | None}
```

## Versions

This package tracks two separate versions:

- **Package version** (`nsjail.__version__`): The Python package version (follows semver)
- **Bundled nsjail** (`nsjail.__nsjail_version__`): The nsjail binary version (from upstream)

## Building

### Prerequisites

```bash
# Build dependencies
apt-get install -y build-essential libprotobuf-dev libnl-route-3-dev

# Python tools
pip install build
```

### Build steps

```bash
# 1. Initialize git submodule
git submodule update --init --recursive

# 2. Build nsjail binary
cd nsjail && make && cd ..

# 3. Build wheel
python -m build --wheel
```

The wheel is created in `dist/`.

### Auditwheel (for distribution)

For PyPI distribution, use `auditwheel` to bundle library dependencies:

```bash
# Install auditwheel
pip install auditwheel

# Repair wheel (bundles shared libraries)
auditwheel repair dist/nsjail-*.whl

# Repaired wheels are in wheelhouse/
ls wheelhouse/
```

This creates self-contained wheels with `musllinux` tags that work across different Linux distributions.

## System Requirements

- **OS**: Linux only
- **Python**: 3.9+ (for installation; not required at runtime)
- **Permissions**: Using nsjail requires CAP_SYS_ADMIN or root

## License

- **nsjail**: Apache-2.0 (see [google/nsjail](https://github.com/google/nsjail))
- **python-nsjail packaging**: Apache-2.0
