#!/bin/sh
# Build script for manylinux containers (glibc-based, RHEL/AlmaLinux)
# This script runs inside manylinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build wheel (py3-none, works for all Python 3.x)
# 3. Run auditwheel repair to vendor .so files and fix manylinux tags

set -euxo pipefail

# Install nsjail build dependencies (per nsjail/README.md)
yum install -y autoconf bison flex libtool libnl3-devel patch pkgconfig protobuf-compiler protobuf-devel

# Note: manylinux_2_34 uses x86-64-v2 by default (GCC 14 on AlmaLinux 9)
# This is acceptable since nsjail requires kernel 5.10+, which implies modern hardware
export ARCH=$(uname -m)

# Build wheel - py3-none tag works for all Python 3.x versions
cd /ws
echo "Building wheel with python3..."
python3 -m build --wheel

# Run auditwheel repair on the wheel
# For x86_64, use --disable-isa-ext-check to skip x86-64-v2 check
# (manylinux_2_34 uses x86-64-v2 by default, but spec requires baseline x86-64)
# This is a known PyPA issue #1725
if [ "$ARCH" = "x86_64" ]; then
    auditwheel repair --disable-isa-ext-check dist/*.whl
else
    auditwheel repair dist/*.whl
fi

# Verify wheels were created
wheel_count=$(ls wheelhouse/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel files were created!"
    exit 1
fi

echo "Successfully built $wheel_count wheel(s):"
ls wheelhouse/*.whl
