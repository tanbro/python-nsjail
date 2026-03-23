#!/bin/sh
# Build script for manylinux containers (glibc-based, RHEL/AlmaLinux)
# This script runs inside manylinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build wheels for multiple Python versions
# 3. Run auditwheel repair to vendor .so files and fix manylinux tags

set -euxo pipefail

# Install nsjail build dependencies (per nsjail/README.md)
yum install -y autoconf bison flex libtool libnl3-devel pkgconfig protobuf-compiler protobuf-devel

# Python versions to build (available in PATH as python3.X)
PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13 3.14"

# Build nsjail binary once (shared across all Python versions)
echo "Building nsjail binary..."
if [ "$ARCH" = "x86_64" ]; then
    # Force baseline x86-64 for manylinux_2_34 compatibility
    # (GCC in manylinux_2_34 defaults to x86-64-v2 which auditwheel rejects)
    echo "Setting CFLAGS/CXXFLAGS for baseline x86-64 (manylinux)"
    make -C /ws/nsjail CFLAGS="$CFLAGS" CXXFLAGS="$CXXFLAGS"
else
    make -C /ws/nsjail
fi

# Build wheel for each Python version
cd /ws
for py_ver in $PYTHON_VERSIONS; do
    echo "Building wheel with python$py_ver..."
    python$py_ver -m build --wheel
done

# Run auditwheel repair on all wheels
for wheel in dist/*.whl; do
    echo "Repairing $wheel..."
    auditwheel repair "$wheel"
done

# Verify wheels were created
wheel_count=$(ls wheelhouse/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel files were created!"
    exit 1
fi

echo "Successfully built $wheel_count wheel(s):"
ls wheelhouse/*.whl
