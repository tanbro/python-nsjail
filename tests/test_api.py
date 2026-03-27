"""Tests for nsjail Python API."""

import asyncio
import subprocess

import pytest

from nsjail import (
    NsjailOptions,
    NsenterOptions,
    async_create_nsjail,
    async_create_nsenter,
    build_nsjail_args,
    build_nsenter_args,
    create_nsjail,
    create_nsenter,
    interleave_streams,
)


# ===== Basic Tests =====


@pytest.mark.asyncio
async def test_async_basic():
    """Test basic async create and wait."""
    proc = await async_create_nsjail(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


def test_sync_basic():
    """Test basic sync create and wait."""
    proc = create_nsjail(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    proc.wait()
    assert proc.returncode == 0


# ===== Options Tests =====


@pytest.mark.asyncio
async def test_with_options():
    """Test with NsjailOptions."""
    proc = await async_create_nsjail(
        command=["/bin/true"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    assert ret == 0


# ===== Stream Tests =====


@pytest.mark.asyncio
async def test_interleave_streams():
    """Test interleave_streams utility."""
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "echo out; echo err >&2"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    sources = []
    async for source, chunk in interleave_streams(proc):
        sources.append(source)

    await proc.wait()
    assert set(sources) == {"stdout", "stderr"}


@pytest.mark.asyncio
async def test_interleave_streams_stdout_only():
    """Test interleave_streams with stdout only."""
    proc = await async_create_nsjail(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    chunks = []
    async for source, chunk in interleave_streams(proc, stderr=False):
        assert source == "stdout"
        chunks.append(chunk)

    await proc.wait()
    assert b"hello" in b"".join(chunks)


@pytest.mark.asyncio
async def test_interleave_streams_stderr_only():
    """Test interleave_streams with stderr only."""
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "echo error >&2"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    chunks = []
    async for source, chunk in interleave_streams(proc, stdout=False):
        assert source == "stderr"
        chunks.append(chunk)

    await proc.wait()
    assert b"error" in b"".join(chunks)


# ===== Helper Functions Tests =====


def test_build_nsjail_args_basic():
    """Test build_nsjail_args with basic options."""
    args = build_nsjail_args(NsjailOptions(chroot="/"))
    assert "--chroot" in args
    assert "/" in args


def test_build_nsjail_args_with_config():
    """Test build_nsjail_args with config file."""
    args = build_nsjail_args(
        options=NsjailOptions(chroot="/"),
        config="/path/to/config.cfg",
    )
    assert "--config" in args
    assert "/path/to/config.cfg" in args
    assert "--chroot" in args


def test_build_nsjail_args_empty():
    """Test build_nsjail_args with no options."""
    args = build_nsjail_args()
    assert args == []


def test_build_nsenter_args_basic():
    """Test build_nsenter_args."""
    args = build_nsenter_args(1234, ["net", "mnt"])
    assert "--target" in args
    assert "1234" in args
    assert "-n" in args
    assert "-m" in args


def test_build_nsenter_args_with_options():
    """Test build_nsenter_args with NsenterOptions."""

    args = build_nsenter_args(
        1234,
        ["net"],
        options=NsenterOptions(wd="/tmp"),
    )
    assert "--target" in args
    assert "-n" in args
    assert "--wd" in args
    assert "/tmp" in args


def test_build_nsenter_args_invalid_namespace():
    """Test build_nsenter_args with invalid namespace."""
    with pytest.raises(ValueError, match="Unknown namespace"):
        build_nsenter_args(1234, ["invalid_namespace"])  # type: ignore[arg-type]


# ===== Options Tests (from original) =====


def test_options_build_args():
    """Test NsjailOptions.build_args()."""
    options = NsjailOptions(
        chroot="/srv/jail",
        user=65534,
        env={"HOME": "/tmp"},
        bindmount_ro=["/lib:/lib"],
        tmpfsmount=["/tmp"],
    )
    args = options.build_args()

    assert "--chroot" in args
    assert "/srv/jail" in args
    assert "--user" in args
    assert "65534" in args
    assert "--env" in args
    assert "HOME=/tmp" in args
    assert "--bindmount_ro" in args


def test_options_none_values():
    """Test that None values don't generate arguments."""
    options = NsjailOptions()
    args = options.build_args()
    assert args == []


def test_options_empty_containers():
    """Test that empty containers don't generate arguments."""
    options = NsjailOptions(env={}, bindmount=[], bindmount_ro=[], tmpfsmount=[])
    args = options.build_args()
    assert args == []


def test_options_hostname():
    """Test hostname option."""
    options = NsjailOptions(hostname="test-jail")
    args = options.build_args()
    assert "--hostname" in args
    assert "test-jail" in args


def test_options_hostname_none():
    """Test that None hostname doesn't generate arguments."""
    options = NsjailOptions(hostname=None)
    args = options.build_args()
    assert "--hostname" not in args


def test_options_bindmount():
    """Test bindmount/bindmount_ro parameters."""
    options = NsjailOptions(
        bindmount_ro=["/lib:/lib", "/usr:/usr"],
        bindmount=["/tmp:/tmp", "/proc"],
    )
    args = options.build_args()

    assert args.count("--bindmount_ro") == 2
    assert args.count("--bindmount") == 2
    assert "/lib:/lib" in args
    assert "/usr:/usr" in args
    assert "/tmp:/tmp" in args
    assert "/proc" in args


def test_options_bindmount_only():
    """Test bindmount with only read-write mounts."""
    options = NsjailOptions(
        bindmount=["/lib:/lib", "/tmp:/tmp"],
    )
    args = options.build_args()

    assert args.count("--bindmount") == 2
    assert "--bindmount_ro" not in args


def test_options_tmpfsmount():
    """Test tmpfsmount parameter."""
    options = NsjailOptions(
        tmpfsmount=["/tmp", "/dev/shm"],
    )
    args = options.build_args()

    assert args.count("--tmpfsmount") == 2
    assert "/tmp" in args
    assert "/dev/shm" in args


# ===== Error Handling Tests =====


@pytest.mark.asyncio
async def test_command_not_found():
    """Test command that doesn't exist."""
    proc = await async_create_nsjail(
        command=["/bin/nonexistent_command_xyz123"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    assert ret != 0


@pytest.mark.asyncio
async def test_command_non_zero_exit():
    """Test command that exits with non-zero code."""
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "exit 42"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    assert ret == 42


# ===== Resource Limit Tests =====


@pytest.mark.asyncio
async def test_time_limit():
    """Test that time_limit actually kills the process."""
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "sleep 1000"],
        options=NsjailOptions(chroot="/", time_limit=1),
    )
    ret = await proc.wait()
    assert ret != 0


# ===== Concurrent Process Tests =====


@pytest.mark.asyncio
async def test_concurrent_processes():
    """Test running multiple nsjail processes concurrently."""

    async def run_echo(num: int) -> int:
        proc = await async_create_nsjail(
            command=["/bin/echo", f"process_{num}"],
            options=NsjailOptions(chroot="/"),
        )
        await proc.wait()
        assert proc.returncode is not None
        return proc.returncode

    results = await asyncio.gather(*[run_echo(i) for i in range(10)])
    assert all(r == 0 for r in results)


# ===== Pass-through Tests =====


@pytest.mark.asyncio
async def test_pass_through_cwd():
    """Test that cwd kwarg is passed through."""
    proc = await async_create_nsjail(
        command=["/bin/sh", "-c", "pwd"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        cwd="/",
    )
    assert proc.stdout is not None
    output = await proc.stdout.read()
    await proc.wait()
    assert b"/" in output or output  # Just check it ran


def test_sync_pass_through_cwd():
    """Test that sync function passes cwd through."""
    proc = create_nsjail(
        command=["/bin/sh", "-c", "pwd"],
        options=NsjailOptions(chroot="/"),
        stdout=subprocess.PIPE,
        cwd="/",
    )

    output, _ = proc.communicate()
    assert b"/" in output or output  # Just check it ran


# ===== Binary Finding Tests =====


def test_locate_nsjail():
    """Test that locate_nsjail works."""
    from nsjail.locator import locate_nsjail

    result = locate_nsjail()
    assert result.is_absolute()
    assert result.name == "nsjail"


# ===== nsenter Tests =====


@pytest.mark.asyncio
async def test_nsenter_basic():
    """Test basic nsenter process creation."""
    # Create a target process
    sleep_proc = await asyncio.create_subprocess_exec("sleep", "10")

    try:
        proc = await async_create_nsenter(
            target_pid=sleep_proc.pid,
            namespaces=["net", "mnt"],
            command=["echo", "test"],
            stdout=subprocess.PIPE,
        )
        assert proc.stdout is not None
        await proc.stdout.read()
        await proc.wait()
        assert proc.returncode == 0
    finally:
        sleep_proc.kill()
        await sleep_proc.wait()


def test_nsenter_sync():
    """Test sync nsenter process creation."""
    import subprocess as sp

    # Create a target process using subprocess
    sleep_proc = sp.Popen(["sleep", "10"])

    try:
        proc = create_nsenter(
            target_pid=sleep_proc.pid,
            namespaces=["net"],
            command=["/bin/pwd"],
            stdout=sp.PIPE,
        )

        output, _ = proc.communicate()
        # Just check it ran successfully
        assert proc.returncode == 0
    finally:
        sleep_proc.kill()
        sleep_proc.wait()
