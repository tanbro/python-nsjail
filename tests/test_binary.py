"""
Tests for the nsjail binary package.

These tests verify that the nsjail binary is correctly installed and functional.
"""

import os
import subprocess
from pathlib import Path

import pytest

import nsjail


def test_package_version():
    """Test that the package versions are accessible."""
    assert hasattr(nsjail, "__version__")
    assert hasattr(nsjail, "__nsjail_version__")

    assert isinstance(nsjail.__version__, str)
    assert isinstance(nsjail.__nsjail_version__, str)

    # Simple version format check
    parts = nsjail.__version__.split(".")
    assert len(parts) >= 2, f"Invalid version format: {nsjail.__version__}"

    # nsjail version should be non-empty
    assert nsjail.__nsjail_version__, "nsjail version should not be empty"


def test_find_system_nsjail():
    """Test that find_system_nsjail() returns expected type."""
    result = nsjail.find_system_nsjail()
    # Should return str or None
    assert result is None or isinstance(result, str)


def test_find_bundled_nsjail():
    """Test that find_bundled_nsjail() returns expected type."""
    result = nsjail.find_bundled_nsjail()
    # Should return Path or None
    assert result is None or isinstance(result, (str, Path))


def test_nsjail_binary_executable():
    """Test that the nsjail binary is executable."""
    # Try bundled first, then system
    nsjail_path = nsjail.find_bundled_nsjail()
    if not nsjail_path:
        nsjail_path = nsjail.find_system_nsjail()

    if not nsjail_path:
        pytest.skip("No nsjail binary found")

    assert os.access(nsjail_path, os.X_OK), (
        f"nsjail binary is not executable: {nsjail_path}"
    )


def test_nsjail_runs():
    """Test that the nsjail binary runs and shows usage."""
    # Try bundled first, then system
    nsjail_path = nsjail.find_bundled_nsjail()
    if not nsjail_path:
        nsjail_path = nsjail.find_system_nsjail()

    if not nsjail_path:
        pytest.skip("No nsjail binary found")

    result = subprocess.run(
        [str(nsjail_path)],
        capture_output=True,
        text=True,
    )
    # Should show usage when no args
    assert "Usage:" in result.stdout or "Usage:" in result.stderr


def test_nsjail_help():
    """Test that nsjail --help works."""
    # Try bundled first, then system
    nsjail_path = nsjail.find_bundled_nsjail()
    if not nsjail_path:
        nsjail_path = nsjail.find_system_nsjail()

    if not nsjail_path:
        pytest.skip("No nsjail binary found")

    result = subprocess.run(
        [str(nsjail_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Usage:" in result.stdout or "Usage:" in result.stderr
