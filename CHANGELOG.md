# CHANGELOG

## [v0.3.0]

📅 2026-03-29

### ✨ Added

- **Complete nsjail options coverage** - `NsjailOptions` now covers 95%+ of nsjail CLI options
  - Execution modes: ONCE, EXECVE, RERUN, LISTEN (TCP server)
  - Full resource limits: all rlimit options (cpu, as, core, fsize, nproc, stack, etc.)
  - cgroup v1/v2 support: memory, pids, cpu, net_cls controllers
  - Networking: macvlan, iface management, pasta (user-mode networking)
  - Mount options: mount, symlink, tmpfsmount with size limits
  - Capabilities and seccomp policy support
  - UID/GID mapping for unprivileged namespaces
  - Logging: multiple verbosity levels, file/fd output
  - Process control: daemon, signals, fd passing
  - `hostname` option for UTS namespace isolation

- **Complete nsenter options coverage** - `NsenterOptions` covers all nsenter CLI options
  - Namespace selection: all or specific namespaces
  - Working directory control: wd, wdns, root
  - User/group management with parent namespace support
  - Credentials and capabilities preservation
  - Environment inheritance from target process
  - Process control: no-fork, cgroup joining
  - SELinux context following

- **ProcessOptionsProtocol** - Type protocol for options consistency

### 🔄 Changed

- **Python-agnostic wheels** - Wheels are now `py3-none-{platform}`, compatible with all Python 3.9+
  - Removed fake C extension stub (`_stub.c`)
  - Wheels work across Python versions without rebuilding

- **Dual sync/async API** - Complete API redesign for consistency
  - Sync: `create_nsjail()`, `create_nsenter()` returning `subprocess.Popen`
  - Async: `async_create_nsjail()`, `async_create_nsenter()` returning `asyncio.subprocess.Process`
  - Helper: `interleave_streams()` for interleaving stdout/stderr in async
  - All `*args` and `**kwargs` passed through to stdlib subprocess functions
  - **EOF signaling**: `interleave_streams()` now yields `b""` on EOF so callers can detect stream end

- **Options naming consistency** - Renamed options to match nsjail CLI naming
  - `clear_env` → `keep_env` (inverted logic for clarity)
  - `cpu_time_limit` → `rlimit_cpu`
  - `memory_limit` → `rlimit_as`
  - `max_pids` → `cgroup_pids_max`
  - `max_open_files` → `rlimit_nofile`

### 🗑️ Removed

- **High-level wrapper classes** - Removed `NsjailProcess` and `NsenterContext`
  - Use stdlib `subprocess.Popen` / `asyncio.subprocess.Process` directly
  - Simpler, more transparent, better IDE support

### 🔧 Internal

- **wheel structure** - Reorganized to comply with wheel spec (Root-Is-Purelib: false)
  - All files now at wheel root instead of `.data` subdirectories
  - Correct rpath for auditwheel-repaired wheels (`$ORIGIN/../../python_nsjail.libs`)
- **CI build** - Simplified to use `uv build --wheel` with single Python version
  - Git ownership detection fix for Docker containers
  - Removed test job from CI (tests require CAP_SYS_ADMIN not available in GitHub Actions)
  - Lint and type check remain in CI for code quality assurance
- **Module reorganization** - Split `process.py` into `subprocess.py` and `async_subprocess.py`
- **Error messages** - Improved binary not found errors with file path information
- **Options organization** - Reorganized with clear section headers for better navigation

## [v0.3.0b2]

📅 2026-03-28

### 🔧 Fixed

- Tests requiring CAP_SYS_ADMIN now properly skipped in GitHub Actions environment

## [v0.3.0b1]

📅 2026-03-28

### ✨ Added

- **Complete nsjail options coverage** - `NsjailOptions` now covers 95%+ of nsjail CLI options
  - Execution modes: ONCE, EXECVE, RERUN, LISTEN (TCP server)
  - Full resource limits: all rlimit options (cpu, as, core, fsize, nproc, stack, etc.)
  - cgroup v1/v2 support: memory, pids, cpu, net_cls controllers
  - Networking: macvlan, iface management, pasta (user-mode networking)
  - Mount options: mount, symlink, tmpfsmount with size limits
  - Capabilities and seccomp policy support
  - UID/GID mapping for unprivileged namespaces
  - Logging: multiple verbosity levels, file/fd output
  - Process control: daemon, signals, fd passing
  - `hostname` option for UTS namespace isolation

- **Complete nsenter options coverage** - `NsenterOptions` covers all nsenter CLI options
  - Namespace selection: all or specific namespaces
  - Working directory control: wd, wdns, root
  - User/group management with parent namespace support
  - Credentials and capabilities preservation
  - Environment inheritance from target process
  - Process control: no-fork, cgroup joining
  - SELinux context following

- **ProcessOptionsProtocol** - Type protocol for options consistency

### 🔄 Changed

- **Python-agnostic wheels** - Wheels are now `py3-none-{platform}`, compatible with all Python 3.9+
  - Removed fake C extension stub (`_stub.c`)
  - Wheels work across Python versions without rebuilding

- **Dual sync/async API** - Complete API redesign for consistency
  - Sync: `create_nsjail()`, `create_nsenter()` returning `subprocess.Popen`
  - Async: `async_create_nsjail()`, `async_create_nsenter()` returning `asyncio.subprocess.Process`
  - Helper: `interleave_streams()` for interleaving stdout/stderr in async
  - All `*args` and `**kwargs` passed through to stdlib subprocess functions
  - **EOF signaling**: `interleave_streams()` now yields `b""` on EOF so callers can detect stream end

- **Options naming consistency** - Renamed options to match nsjail CLI naming
  - `clear_env` → `keep_env` (inverted logic for clarity)
  - `cpu_time_limit` → `rlimit_cpu`
  - `memory_limit` → `rlimit_as`
  - `max_pids` → `cgroup_pids_max`
  - `max_open_files` → `rlimit_nofile`

### 🗑️ Removed

- **High-level wrapper classes** - Removed `NsjailProcess` and `NsenterContext`
  - Use stdlib `subprocess.Popen` / `asyncio.subprocess.Process` directly
  - Simpler, more transparent, better IDE support

### 🔧 Internal

- **wheel structure** - Reorganized to comply with wheel spec (Root-Is-Purelib: false)
  - All files now at wheel root instead of `.data` subdirectories
  - Correct rpath for auditwheel-repaired wheels (`$ORIGIN/../../python_nsjail.libs`)
- **CI build** - Simplified to use `uv build --wheel` with single Python version
  - Git ownership detection fix for Docker containers
- **Module reorganization** - Split `process.py` into `subprocess.py` and `async_subprocess.py`
- **Error messages** - Improved binary not found errors with file path information
- **Options organization** - Reorganized with clear section headers for better navigation

## [v0.3.0a1]

📅 2026-03-25

### 🔄 Changed

- **Python-agnostic wheels** - Wheels are now `py3-none-{platform}`, compatible with all Python 3.9+
  - Removed fake C extension stub (`_stub.c`)
  - Wheels work across Python versions without rebuilding

- **Dual sync/async API** - Complete API redesign for consistency
  - Sync: `create_nsjail()`, `create_nsenter()` returning `subprocess.Popen`
  - Async: `async_create_nsjail()`, `async_create_nsenter()` returning `asyncio.subprocess.Process`
  - Helper: `interleave_streams()` for interleaving stdout/stderr in async
  - All `*args` and `**kwargs` passed through to stdlib subprocess functions

### 🗑️ Removed

- **High-level wrapper classes** - Removed `NsjailProcess` and `NsenterContext`
  - Use stdlib `subprocess.Popen` / `asyncio.subprocess.Process` directly
  - Simpler, more transparent, better IDE support

### 🔧 Internal

- **wheel structure** - Reorganized to comply with wheel spec (Root-Is-Purelib: false)
  - All files now at wheel root instead of `.data` subdirectories
  - Correct rpath for auditwheel-repaired wheels (`$ORIGIN/../../python_nsjail.libs`)
- **CI build** - Simplified to use `uv build --wheel` with single Python version
- **Module reorganization** - Split `process.py` into `subprocess.py` and `async_subprocess.py`

## [v0.2.0]
