"""Tests for nsjail Python API."""

import pytest

from nsjail import NsjailOptions, start


@pytest.mark.asyncio
async def test_start_basic():
    """Test basic start and wait."""
    proc = await start(
        command="/bin/echo",
        args=["hello"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_start_with_options():
    """Test start with NsjailOptions."""
    proc = await start(
        command="/bin/true",
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_stream_output():
    """Test streaming stdout with chroot."""
    proc = await start(
        command="/bin/echo",
        args=["hello world"],
        options=NsjailOptions(chroot="/"),
    )
    chunks = []
    async for source, chunk in proc.stream():
        chunks.append((source, chunk))

    # Should have both stdout and stderr (nsjail logs)
    assert len(chunks) > 0
    assert any(source == "stdout" for source, _ in chunks)
    assert any(source == "stderr" for source, _ in chunks)
    # Should have our output
    assert any(b"hello world" in chunk for _, chunk in chunks)


@pytest.mark.asyncio
async def test_auto_print():
    """Test auto_print parameter."""
    proc = await start(command="/bin/echo", args=["test"], auto_print=True)
    await proc.wait()
    # Should have printed, we just check it doesn't crash


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    async with await start(
        command="/bin/sleep",
        args=["0.1"],
        options=NsjailOptions(chroot="/"),
    ) as proc:
        assert proc.pid > 0
        assert proc.is_running()
    # Should be terminated after context exit


@pytest.mark.asyncio
async def test_terminate():
    """Test terminate method."""
    proc = await start(
        command="/bin/sleep",
        args=["3600"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.is_running()
    proc.terminate()
    await proc.wait()
    assert not proc.is_running()


def test_options_build_args():
    """Test NsjailOptions.build_args()."""
    options = NsjailOptions(
        chroot="/srv/jail",
        user=65534,
        env={"HOME": "/tmp"},
        mounts=[("/lib", "/lib", "ro")],
        tmpfs=["/tmp"],
    )
    args = options.build_args()

    assert "-Mo" in args
    assert "-c" in args
    assert "/srv/jail" in args
    assert "-u" in args
    assert "65534" in args
    assert "--env" in args
    assert "HOME=/tmp" in args
    assert "-R" in args


def test_options_none_values():
    """Test that None values don't generate arguments."""
    options = NsjailOptions()
    args = options.build_args()

    # Should only have -Mo
    assert args == ["-Mo"]


def test_options_empty_containers():
    """Test that empty containers don't generate arguments."""
    options = NsjailOptions(env={}, mounts=[], tmpfs=[])
    args = options.build_args()

    # Should only have -Mo
    assert args == ["-Mo"]


def test_options_mounts():
    """Test mounts parameter."""
    options = NsjailOptions(
        mounts=[
            ("/lib", "/lib", "ro"),
            ("/tmp", "/tmp", "rw"),
        ]
    )
    args = options.build_args()

    assert "-R" in args
    assert "/lib:/lib" in args or "/lib" in args
    assert "-B" in args
    assert "/tmp:/tmp" in args or "/tmp" in args
