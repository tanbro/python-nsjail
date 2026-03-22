#!/bin/bash
# Build script for manylinux containers (glibc-based, RHEL/AlmaLinux)
# This script runs inside manylinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Install Python build tools
# 3. Build the Python wheel (setup.py compiles nsjail automatically)
# 4. Run auditwheel repair to vendor .so files and fix manylinux tags

set -euxo pipefail

# Install nsjail build dependencies
yum install -y protobuf-devel libnl3-devel protobuf-compiler

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
