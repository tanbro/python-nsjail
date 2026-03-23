#!/bin/sh
# Build script for manylinux containers (glibc-based, RHEL/AlmaLinux)
# This script runs inside manylinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build wheels for multiple Python versions
# 3. Run auditwheel repair to vendor .so files and fix manylinux tags

set -euxo pipefail

# Install nsjail build dependencies (per nsjail/README.md)
yum install -y autoconf bison flex libtool libnl3-devel pkgconfig protobuf-compiler protobuf-devel

# Force baseline x86-64 for manylinux_2_34 compatibility
# (GCC in manylinux_2_34 defaults to x86-64-v2 which auditwheel rejects)
export ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    export CFLAGS="-march=x86-64"
    export CXXFLAGS="-march=x86-64"
    echo "Setting CFLAGS/CXXFLAGS for baseline x86-64 (manylinux)"
fi

# Python versions to build (available in PATH as python3.X)
PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13 3.14"

# Build wheels - setuptools will compile nsjail via BuildExtCommand
cd /ws
for py_ver in $PYTHON_VERSIONS; do
    echo "Building wheel with python$py_ver..."
    if [ "$ARCH" = "x86_64" ]; then
        # Use --no-isolation to preserve CFLAGS/CXXFLAGS for nsjail compilation
        # (isolated environment strips environment variables)
        python$py_ver -m build --wheel --no-isolation
    else
        # aarch64 doesn't need special flags, can use isolated build
        python$py_ver -m build --wheel
    fi
done

# Run auditwheel repair on all wheels
auditwheel repair dist/*.whl

# Verify wheels were created
wheel_count=$(ls wheelhouse/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel files were created!"
    exit 1
fi

echo "Successfully built $wheel_count wheel(s):"
ls wheelhouse/*.whl
