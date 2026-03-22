#!/bin/bash
# Build script for musllinux containers (musl-based, Alpine)
# This script runs inside musllinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build the Python wheel (custom build command compiles nsjail)
# 3. Run auditwheel repair to vendor .so files and fix musllinux tags

set -euxo pipefail

# musllinux images are Alpine-based, so we use apk
# Update package index
apk update

# Install nsjail build dependencies
apk add \
    protobuf-dev \
    libnl3-dev \
    protobuf-compiler \
    g++ \
    make \
    pkgconf

# Build Python wheel
# The custom build command in setup.py will compile nsjail automatically
cd /ws
python -m build --wheel

# Run auditwheel repair
# This will:
# 1. Scan the wheel for shared library dependencies
# 2. Vendor .so files into nsjail.libs/
# 3. Fix RPATH to $ORIGIN/nsjail.libs
# 4. Update the WHEEL file with proper musllinux tags
# 5. Output to wheelhouse/
auditwheel repair dist/*.whl

# Move repaired wheels to dist/ for artifact upload
mv wheelhouse/*.whl dist/

# Show the results
ls -la dist/

# Verify the wheel was created
wheel_count=$(ls dist/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel file was created!"
    exit 1
fi

echo "Successfully built wheel(s):"
ls dist/*.whl
