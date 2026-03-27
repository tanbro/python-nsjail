"""
Tests for the nsjail binary package.

These tests verify that the nsjail binary is correctly installed and functional.
"""

import os
import subprocess
from pathlib import Path


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


def test_locate_nsjail():
    """Test that locate_nsjail() returns a Path."""
    result = nsjail.locate_nsjail()
    assert isinstance(result, Path)


def bundled_nsjail():
    """Test that bundled_binary() returns a Path."""
    result = nsjail.bundled_nsjail()
    assert isinstance(result, Path)


def test_scripts_nsjail():
    """Test that console_script() returns expected type."""
    result = nsjail.scripts_nsjail()
    # May not exist in all environments
    assert result is None or isinstance(result, Path)


def test_bundled_nsjail_executable():
    """Test that the nsjail binary is executable."""
    nsjail_path = nsjail.bundled_nsjail()
    assert os.access(nsjail_path, os.X_OK), (
        f"nsjail binary is not executable: {nsjail_path}"
    )


def test_nsjail_runs():
    """Test that the nsjail binary runs and shows usage."""
    nsjail_path = nsjail.bundled_nsjail()

    result = subprocess.run(
        [str(nsjail_path)],
        capture_output=True,
        text=True,
    )
    # Should show usage when no args
    assert "Usage:" in result.stdout or "Usage:" in result.stderr


def test_nsjail_help():
    """Test that nsjail --help works."""
    nsjail_path = nsjail.bundled_nsjail()

    result = subprocess.run(
        [str(nsjail_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Usage:" in result.stdout or "Usage:" in result.stderr
