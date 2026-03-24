# CHANGELOG

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
