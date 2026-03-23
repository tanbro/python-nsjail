#!/bin/sh
# Build script for musllinux containers (musl-based, Alpine)
# This script runs inside musllinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build wheels for multiple Python versions
# 3. Run auditwheel repair to vendor .so files and fix musllinux tags

set -euxo pipefail

# musllinux images are Alpine-based, so we use apk
apk update

# Install nsjail build dependencies (per nsjail/README.md)
apk add autoconf bison flex libtool libnl3-dev pkgconf protoc protobuf-dev

# Python versions to build (available in PATH as python3.X)
PYTHON_VERSIONS="3.9 3.10 3.11 3.12 3.13 3.14"

# Build wheels - setuptools will compile nsjail via BuildExtCommand
cd /ws
for py_ver in $PYTHON_VERSIONS; do
    echo "Building wheel with python$py_ver..."
    python$py_ver -m build --wheel
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
