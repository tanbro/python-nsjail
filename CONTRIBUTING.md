# Contributing to python-nsjail

Thank you for your interest in contributing!

## Development Setup

### Using uv (Recommended)

```bash
# Clone with submodules
git clone --recursive https://github.com/tanbro/python-nsjail
cd python-nsjail

# Install with dev dependencies
uv sync
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

# Install the package
pip install -e .
```

**IMPORTANT**: Strongly recommend using a virtual environment for development.

## Building

### Prerequisites

**System dependencies** (Debian/Ubuntu):
```bash
sudo apt-get install autoconf bison flex gcc g++ git libprotobuf-dev libnl-route-3-dev libtool make pkg-config protobuf-compiler
```

See [nsjail README](https://github.com/google/nsjail) for full build requirements.

Install **Python build tools** if your are using pip:
```bash
pip install build
```

### Build Steps

```bash
# 1. Update submodule
git submodule update --init --recursive

# 2. Build wheel (compiles nsjail and bundles it)
#   Using uv:  uv build --wheel
#   Using pip: python -m build --wheel
uv build --wheel
```

> **Note for developers**: After cloning the repository, you must build the wheel at least once before running tests or importing the package. The build process compiles the nsjail binary and places it at `src/nsjail/bin/nsjail`, which is required for the package to function.

```bash
# 3. Verify installation
#   Using uv:  uv pip install dist/*.whl
#   Using pip: pip install dist/*.whl
uv pip install dist/python_nsjail-*.whl
nsjail-status
```

## Testing

```bash
# Run tests
pytest

# Or with verbose output
pytest -v

# Run specific test
pytest tests/test_api.py::test_sync_basic
```

## Code Quality

Before submitting changes, run the full pre-commit check:

```bash
pre-commit run -a --all-files
```

This includes:
- **ruff** - linting and formatting
- **mypy** - static type checking
- **yaml/toml validation** - config file checks

### Type Safety

This project uses strict type checking with `mypy`. When adding new code:

- Use explicit type annotations for public functions
- Use `dict[Literal["a", "b"], Type]` pattern for dictionaries with literal key types
- Avoid `Any` - use specific types or `TypeVar` when needed

### Code Style

- **Imports at module top** - All imports should be at the beginning of modules
- **Simple functions over classes** - Prefer functions over complex wrapper classes
- **Explicit over implicit** - Make behavior clear, not hidden
- **Docstrings** - Use Google-style docstrings for public APIs

## API Design Principles

This project follows these design principles:

1. **Simple functions** - Use `create_foo()` instead of `FooBuilder` classes
2. **Dual ecosystem** - Support both sync and async APIs
3. **Transparent** - Pass `*args, **kwargs` through to stdlib
4. **No magic** - Don't hide important behavior

Example:
```python
# Good: simple function with transparent pass-through
def create_nsjail(command, options=None, *args, **kwargs):
    return subprocess.Popen(cmd, *args, **kwargs)

# Avoid: complex wrapper with hidden behavior
class NsjailBuilder:
    def create(self, mode="async"):
        if mode == "async":
            return self._create_async()
        # ...
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

3. Update `src/nsjail/version.py`:
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
5. Ensure `pre-commit run -a --all-files` passes
6. Submit a pull request

## Release Process

This project uses git-flow for branching and version management. Tag format follows git-flow conventions with `v` prefix (e.g., `v0.3.0b1`), which is automatically added by git-flow.

**Version format**: `X.Y.Z{pre}` where `pre` can be:
- `aN` (alpha): `v0.3.0a1`
- `bN` (beta): `v0.3.0b1`
- `rcN` (release candidate): `v0.3.0rc1`
- (no suffix): stable release: `v0.3.0`

**PyPI compatibility**: PyPI strips the `v` prefix when displaying versions, so `v0.3.0b1` becomes `0.3.0b1` on PyPI.

**Release steps**:
```bash
# 1. Start release branch (version without v prefix)
git flow release start 0.3.0b1

# 2. Update CHANGELOG.md in the release branch
# Edit version number and date

# 3. Finish release (creates tag v0.3.0b1)
git flow release finish 0.3.0b1

# 4. Push tags and branches
git push origin main
git push origin develop
git push origin v0.3.0b1
```

**Important**: When using `git flow release start`, use the version **without** the `v` prefix (e.g., `0.3.0b1`, not `v0.3.0b1`). Git-flow will automatically add the `v` prefix when creating the tag.

### Commit Message Format

Use clear, descriptive commit messages:

```
refactor: brief description

Detailed explanation of what changed and why.

- Changed file or component
- Added feature or fix

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

Common prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code restructuring without behavior change
- `docs:` - Documentation updates
- `test:` - Test additions or changes

### Pull Request Checklist

- [ ] Tests added/updated for new functionality
- [ ] `pre-commit run -a --all-files` passes
- [ ] Documentation updated (README, docstrings)
- [ ] Project structure section updated if adding new files
- [ ] Version bumped if breaking changes

## Project Structure

```
python-nsjail/
├── nsjail/                    # git submodule (upstream source)
├── src/
│   └── nsjail/                # Python package
│       ├── __init__.py        # API exports
│       ├── version.py         # Version info
│       ├── subprocess.py       # Sync subprocess functions
│       ├── async_subprocess.py # Async subprocess functions
│       ├── locator.py         # Binary location utilities
│       ├── options.py         # NsjailOptions, NsenterOptions
│       └── bin/               # Created during build
├── tests/
│   └── test_api.py            # API tests
├── CONTRIBUTING.md            # This file
├── README.md                  # User documentation
└── pyproject.toml            # Build config
```

## Project Philosophy

This project follows these design principles:

1. **Simple functions over classes** - Use `create_foo()` instead of builder classes
2. **Dual ecosystem** - Support both sync and async APIs
3. **Transparent** - Pass `*args, **kwargs` through to stdlib
4. **Explicit over implicit** - Make behavior clear
5. **Early stage project** - Breaking changes acceptable, prefer clean API

### Code Style

- **Imports at module top** - All imports should be at the beginning of modules
- **Docstrings** - Use Google-style docstrings for public APIs
- **Type hints** - Required for all public functions
- **Avoid magic** - Don't hide important behavior

### Version Management

Two versions are tracked separately in `src/nsjail/version.py`:
- `__version__` - Python package version (semver)
- `__nsjail_version__` - Bundled nsjail binary version

Update independently when appropriate.
