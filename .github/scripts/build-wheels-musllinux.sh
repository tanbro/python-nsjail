#!/bin/bash
# Build script for musllinux containers (musl-based, Alpine)
# This script runs inside musllinux Docker images to:
# 1. Install nsjail build dependencies
# 2. Build the Python wheel (setup.py compiles nsjail automatically)
# 3. Run auditwheel repair to vendor .so files and fix musllinux tags

set -euxo pipefail

# musllinux images are Alpine-based, so we use apk
apk update

# Install nsjail build dependencies
apk add protobuf-dev libnl3-dev protobuf-compiler

# Build Python wheel
cd /ws
python -m build --wheel

# Run auditwheel repair to vendor .so files and fix musllinux tags
auditwheel repair dist/*.whl

# Move repaired wheels to dist/ for artifact upload
mv wheelhouse/*.whl dist/

# Verify the wheel was created
wheel_count=$(ls dist/*.whl 2>/dev/null | wc -l)
if [ "$wheel_count" -eq 0 ]; then
    echo "ERROR: No wheel file was created!"
    exit 1
fi

echo "Successfully built wheel(s):"
ls dist/*.whl
