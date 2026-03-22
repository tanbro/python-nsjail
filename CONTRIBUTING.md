# Contributing to python-nsjail

Thank you for your interest in contributing!

## Development Setup

### Using uv (Recommended)

```bash
# Clone with submodules
git clone --recursive https://github.com/tanbro/python-nsjail
cd python-nsjail

# Install with dev dependencies
uv sync"
```

### Using pip

```bash
# Clone with submodules
git clone --recursive https://github.com/tanbro/python-nsjail
cd python-nsjail

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install build tool
pip install build

# Install with dev dependencies
pip install -e ".[dev]"
```

**IMPORTANT**: Strongly recommend using a virtual environment for development.

## Building

### Prerequisites

**System dependencies** (Debian/Ubuntu):
```bash
sudo apt-get install autoconf bison flex gcc g++ git libprotobuf-dev libnl-route-3-dev libtool make pkg-config protobuf-compiler
```

See [nsjail README](https://github.com/google/nsjail) for full build requirements.

Install **Python tools** if your are using pip:
```bash
pip install build
```

### Build Steps

```bash
# 1. Update submodule
git submodule update --init --recursive

# 2. Build nsjail binary
cd nsjail && make && cd ..

# 3. Build wheel
#   Using uv:  uv build --wheel
#   Using pip: python -m build --wheel
uv build --wheel

# 4. Verify
#   Using uv:  uv pip install dist/nsjail-*.whl
#   Using pip: pip install dist/nsjail-*.whl
uv pip install dist/nsjail-*.whl
nsjail-status
```

## Testing

```bash
# Run tests
pytest

# Or with verbose output
pytest -v
```

## Updating nsjail Version

1. Update the submodule:
   ```bash
   git submodule update --remote nsjail
   ```

2. Verify the version:
   ```bash
   cd nsjail
   git describe --tags --abbrev=0
   ```

3. Update `src/nsjail/__init__.py`:
   ```python
   __version__ = "1.0.0"           # Bump if needed
   __nsjail_version__ = "3.6"      # New nsjail version
   ```

4. Build and test.

## Auditwheel (for PyPI)

For distribution, bundle shared libraries with auditwheel:

```bash
# Using uv:
uv pip install auditwheel
auditwheel repair dist/nsjail-*.whl

# Using pip:
pip install auditwheel
auditwheel repair dist/nsjail-*.whl
```

Repaired wheels are in `wheelhouse/`.

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Ensure tests pass
6. Submit a pull request
