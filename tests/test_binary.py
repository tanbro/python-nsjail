"""
Tests for the nsjail binary package.

These tests verify that the nsjail binary is correctly installed and functional.
"""

import os
import subprocess

import pytest

import nsjail


def test_nsjail_status():
    """Test that status() returns expected structure."""
    info = nsjail.status()
    assert isinstance(info, dict)
    # At least one of system/package/dev should be found
    # But in CI/production, package should exist
    assert "system" in info or "package" in info or "dev" in info


def test_nsjail_binary_executable():
    """Test that the nsjail binary is executable."""
    info = nsjail.status()

    # Test package binary if available
    if "package" in info:
        assert os.access(info["package"], os.X_OK), (
            f"nsjail binary is not executable: {info['package']}"
        )
    elif "dev" in info:
        assert os.access(info["dev"], os.X_OK), (
            f"nsjail binary is not executable: {info['dev']}"
        )
    elif "system" in info:
        assert os.access(info["system"], os.X_OK), (
            f"nsjail binary is not executable: {info['system']}"
        )
    else:
        pytest.skip("No nsjail binary found")


def test_nsjail_runs():
    """Test that the nsjail binary runs and shows usage."""
    info = nsjail.status()

    nsjail_path = info.get("package") or info.get("dev") or info.get("system")
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
    info = nsjail.status()

    nsjail_path = info.get("package") or info.get("dev") or info.get("system")
    if not nsjail_path:
        pytest.skip("No nsjail binary found")

    result = subprocess.run(
        [str(nsjail_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert "Usage:" in result.stdout or "Usage:" in result.stderr


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
