#!/bin/bash
# Build script for manylinux containers (glibc-based, RHEL/AlmaLinux)
# This script runs inside manylinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Install Python build tools
# 3. Build the Python wheel (setup.py compiles nsjail automatically)
# 4. Run auditwheel repair to vendor .so files and fix manylinux tags

set -euxo pipefail

# Install nsjail build dependencies (per nsjail/README.md)
yum install -y autoconf bison flex libtool libnl3-devel pkgconfig protobuf-compiler protobuf-devel

# Force baseline x86-64 for manylinux_2_34 compatibility
# (GCC in manylinux_2_34 defaults to x86-64-v2 which auditwheel rejects)
# Only apply to x86_64; aarch64 doesn't have this issue
export ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    export CFLAGS="-march=x86-64"
    export CXXFLAGS="-march=x86-64"
    echo "Setting CFLAGS/CXXFLAGS for baseline x86-64 (manylinux)"
fi

# Build Python wheel using uv (pre-installed in manylinux images)
cd /ws
uv build --wheel

# Run auditwheel repair to vendor .so files and fix manylinux tags
auditwheel repair dist/*.whl

# Verify the wheel was created
wheel_count=$(ls wheelhouse/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel file was created!"
    exit 1
fi

echo "Successfully built wheel(s):"
ls wheelhouse/*.whl
