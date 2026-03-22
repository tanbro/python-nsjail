#!/bin/bash
# Unified build script for manylinux/musllinux containers
# This script runs inside Docker images to:
# 1. Install nsjail build dependencies
# 2. Build the Python wheel (setup.py compiles nsjail automatically)
# 3. Run auditwheel repair to vendor .so files and fix platform tags

set -euxo pipefail

# Detect package manager and install dependencies
if command -v apk >/dev/null 2>&1; then
    # musllinux (Alpine-based)
    apk update
    apk add protobuf-dev libnl3-dev protobuf-compiler
elif command -v yum >/dev/null 2>&1; then
    # manylinux (RHEL-based)
    yum install -y protobuf-devel libnl3-devel protobuf-compiler
else
    echo "ERROR: Unsupported package manager"
    exit 1
fi

# Build Python wheel
# The custom build command in setup.py will compile nsjail automatically
cd /ws
python -m build --wheel

# Run auditwheel repair
# This will:
# 1. Scan the wheel for shared library dependencies
# 2. Vendor .so files into nsjail.libs/
# 3. Fix RPATH to point to bundled libraries
# 4. Update the WHEEL file with proper manylinux/musllinux tags
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
