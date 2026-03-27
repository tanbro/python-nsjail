# CHANGELOG

## [v0.3.0-a1]

📅 Unreleased

### 🔄 Changed

- **Python-agnostic wheels** - Wheels are now `py3-none-{platform}`, compatible with all Python 3.9+
  - Removed fake C extension stub (`_stub.c`)
  - Wheels work across Python versions without rebuilding

### 🔧 Internal

- **wheel structure** - Reorganized to comply with wheel spec (Root-Is-Purelib: false)
  - All files now at wheel root instead of `.data` subdirectories
  - Correct rpath for auditwheel-repaired wheels (`$ORIGIN/../../python_nsjail.libs`)
- **CI build** - Simplified to use `uv build --wheel` with single Python version
- **Function renamed** - `merge_streams()` → `interleave_streams()` for clarity

## [v0.2.0]

📅 Released 2025-03-25

### ✨ Added

- **nsenter integration** - Execute commands inside existing container namespaces
  - `create_nsenter_process()` - Create process via nsenter command
  - `NsenterOptions` - Configuration for nsenter (cwd, env)
  - Support for all namespace types: net, mnt, ipc, uts, pid, user, cgroup

- **stdin write support** - Interactive process communication
  - `write(data: bytes)` - Async write with drain (wait for flush)
  - `write_nowait(data: bytes)` - Non-blocking write to buffer
  - `writable_stdin` parameter - Control stdin connection in factory functions

- **`nsjail-status` command** - Display installation and binary location info

### 🔄 Changed

- **API simplification** - Merged `command` and `args` into single `command: Sequence[str]` parameter
  - Before: `create_nsjail_process(command="/bin/echo", args=["hello"])`
  - After: `create_nsjail_process(command=["/bin/echo", "hello"])`

- **stream() state management** - Simplified by removing mutual exclusion lock
  - Always queue data (regardless of stream activity)
  - Check EOF state instead of tracking active stream

- **Default buffer settings** - Optimized for sandbox service scenarios
  - `buffer_size`: 65536 → 256 (queue items, ~2MB per process)
  - `chunk_size`: 1024 → 8192 (better I/O efficiency, lower latency)

### 🗑️ Removed

- **Unused modules** - Cleaned up redundant code
  - `NamespaceContext` - Untested Python 3.12+ programmatic namespace entry
  - `nsenter.py` wrapper module - Functionality moved to process.py
  - `_compat.py` ctypes fallback - Only used by removed context.py

### 📚 Documentation

- **README badges** - CI, GitHub release, PyPI version, Python version, license
- **pyproject.toml** - Enhanced classifiers and project URLs (Documentation, Bug Tracker, Changelog)

### ✅ Tests

- Added comprehensive tests for nsenter functionality
- Added stdin write/read tests
- Improved test coverage to 45 tests

## [v0.1.1]

📅 Released 2025-03-24

### ✨ Added

- **Async Python API** for programmatic nsjail process management
  - `create_nsjail_process()` - Create and manage nsjail subprocesses
  - `NsjailProcess` class - Async process wrapper with streaming support
  - `stream()` method - Stream stdout/stderr with preserved ordering
  - Context manager support (`async with`) for automatic cleanup

- 🌍 **Environment variable** `NSJAIL` - Override nsjail binary path
  - Supports `~` and `$VAR` expansion

- 🔧 **Helper functions** for binary location:
  - `locate_nsjail()` - Smart binary location with env var support
  - `bundled_binary()` - Get bundled nsjail path
  - `console_script()` - Get wrapper script path

- 📊 **`nsjail-status` command** - Display installation status
- 🧪 **Code coverage** - `.coveragerc` configuration

### 🔄 Changed

- 📂 **Module rename**: `find.py` → `locator.py` for clearer naming
- 🏷️ **Function rename**: `get_nsjail_path` → `locate_nsjail` for consistency
- ⭕ **Queue semantics**: Ring buffer (discard oldest) instead of blocking when full
- 🔚 **EOF handling**: Use `set` to track EOF from both stdout/stderr
- 🛡️ **Fallback EOF**: Ensure EOF markers sent even if reader tasks cancelled

### 🐛 Fixed

- 📦 **typing-extensions**: Fixed package name (`typing-extension` → `typing-extensions`)
- ❌ **Redundant flag**: Removed `-Mo` flag (nsjail default is MODE_STANDALONE_ONCE)

### ⚡ Improved

- ✅ **Test coverage**: 477 lines of tests for Python API
- 📚 **Documentation**: README reorganized for clarity
- 🛠️ **Linter configs**: Updated ruff, mypy configurations
- 💬 **Error messages**: More descriptive FileNotFoundError messages

### 🔧 Internal

- 📦 Imports now use wildcard from submodules
- 🎯 Better separation of concerns (locator, status, process)

## [v0.1.0]

📅 Released 2025-03-23

### ✨ Added

- 🎉 Initial release
- 📦 Prebuilt nsjail binaries (Linux x86_64, aarch64)
- 🔧 `nsjail` command wrapper
- ⛰️ Basic mount options support
