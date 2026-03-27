#!/bin/sh
# Build script for musllinux containers (musl-based, Alpine)
# This script runs inside musllinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build wheel (py3-none, works for all Python 3.x)
# 3. Run auditwheel repair to vendor .so files and fix musllinux tags

set -euxo pipefail

# musllinux images are Alpine-based, so we use apk
apk update

# Install nsjail build dependencies (per nsjail/README.md)
apk add autoconf bison flex libtool libnl3-dev pkgconf protoc protobuf-dev

# Install Python build tool
pip install --disable-pip-version-check build

# Build wheel - py3-none tag works for all Python 3.x versions
cd /ws
echo "Building wheel with python3..."
python3 -m build --wheel

# Run auditwheel repair on the wheel
auditwheel repair dist/*.whl

# Verify wheels were created
wheel_count=$(ls wheelhouse/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel files were created!"
    exit 1
fi

echo "Successfully built $wheel_count wheel(s):"
ls wheelhouse/*.whl
