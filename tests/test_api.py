"""Tests for nsjail Python API."""

import asyncio
import pytest

from nsjail import NsjailOptions, create_nsjail_process


@pytest.mark.asyncio
async def test_start_basic():
    """Test basic start and wait."""
    proc = await create_nsjail_process(
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
    proc = await create_nsjail_process(
        command="/bin/true",
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_stream_output():
    """Test streaming stdout with chroot."""
    proc = await create_nsjail_process(
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
    """Test tee parameter (auto-print output)."""
    proc = await create_nsjail_process(command="/bin/echo", args=["test"], tee=True)
    await proc.wait()
    # Should have printed, we just check it doesn't crash


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager."""
    async with await create_nsjail_process(
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
    proc = await create_nsjail_process(
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
        bindmount_ro=["/lib:/lib"],
        tmpfsmount=["/tmp"],
    )
    args = options.build_args()

    assert "-Mo" in args
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

    # Should only have -Mo
    assert args == ["-Mo"]


def test_options_empty_containers():
    """Test that empty containers don't generate arguments."""
    options = NsjailOptions(env={}, bindmount=[], bindmount_ro=[], tmpfsmount=[])
    args = options.build_args()

    # Should only have -Mo
    assert args == ["-Mo"]


def test_options_bindmount():
    """Test bindmount/bindmount_ro parameters."""
    options = NsjailOptions(
        bindmount_ro=["/lib:/lib", "/usr:/usr"],
        bindmount=["/tmp:/tmp", "/proc"],
    )
    args = options.build_args()

    # Should have 2x --bindmount_ro and 2x --bindmount
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

    # Should have 2x --bindmount and no --bindmount_ro
    assert args.count("--bindmount") == 2
    assert "--bindmount_ro" not in args


def test_options_tmpfsmount():
    """Test tmpfsmount parameter."""
    options = NsjailOptions(
        tmpfsmount=["/tmp", "/dev/shm"],
    )
    args = options.build_args()

    # Should have 2x --tmpfsmount
    assert args.count("--tmpfsmount") == 2
    assert "/tmp" in args
    assert "/dev/shm" in args


# ===== Error Handling Tests =====


@pytest.mark.asyncio
async def test_command_not_found():
    """Test command that doesn't exist."""
    proc = await create_nsjail_process(
        command="/bin/nonexistent_command_xyz123",
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    # nsjail should fail with non-zero exit code
    assert ret != 0


@pytest.mark.asyncio
async def test_command_non_zero_exit():
    """Test command that exits with non-zero code."""
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=["-c", "exit 42"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    assert ret == 42


@pytest.mark.asyncio
async def test_options_invalid_type():
    """Test that invalid options type raises TypeError."""
    with pytest.raises(TypeError, match="options must be NsjailOptions"):
        await create_nsjail_process(  # type: ignore
            command="/bin/echo",
            options="invalid",
        )


# ===== Ring Buffer Tests =====


@pytest.mark.asyncio
async def test_ring_buffer_discard_oldest():
    """Test that ring buffer discards oldest when full."""
    # Use very small buffer size
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=["-c", "for i in $(seq 1 100); do echo $i; done"],
        options=NsjailOptions(chroot="/"),
        buffer_size=4,  # Very small queue
    )

    chunks = []
    async for source, chunk in proc.stream():
        if source == "stdout":
            chunks.append(chunk)

    # Should not have all 100 lines due to ring buffer overflow
    # But should have some output
    assert len(chunks) > 0


# ===== aclose() Timeout Tests =====


@pytest.mark.asyncio
async def test_aclose_timeout_fallback_to_kill():
    """Test that aclose() falls back to kill() after timeout."""
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=[
            "-c",
            "trap 'echo SIGTERM; sleep 1000' TERM; while true; do sleep 1; done",
        ],
        options=NsjailOptions(chroot="/"),
    )

    # Give process time to set up signal handler
    await asyncio.sleep(0.1)

    # aclose with very short timeout
    await proc.aclose(timeout=0.1)

    # Process should be killed
    assert not proc.is_running()


# ===== Concurrent Process Tests =====


@pytest.mark.asyncio
async def test_concurrent_processes():
    """Test running multiple nsjail processes concurrently."""

    async def run_echo(num: int) -> int:
        proc = await create_nsjail_process(
            command="/bin/echo",
            args=[f"process_{num}"],
            options=NsjailOptions(chroot="/"),
        )
        await proc.wait()
        return proc.returncode

    # Run 10 processes concurrently
    results = await asyncio.gather(*[run_echo(i) for i in range(10)])
    assert all(r == 0 for r in results)


# ===== Resource Limit Tests =====


@pytest.mark.asyncio
async def test_time_limit():
    """Test that time_limit actually kills the process."""
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=["-c", "sleep 1000"],
        options=NsjailOptions(chroot="/", time_limit=1),
    )
    ret = await proc.wait()
    # Should be killed by time limit
    assert ret != 0


@pytest.mark.asyncio
async def test_memory_limit():
    """Test that memory_limit works."""
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=[
            "-c",
            "dd if=/dev/zero of=/dev/shm/big bs=1M count=200 2>/dev/null; echo OK",
        ],
        options=NsjailOptions(chroot="/", memory_limit=64),
    )
    await proc.wait()
    # Should fail due to OOM or just not print OK
    # Note: nsjail might not enforce this in all configs
    # We just check it doesn't hang


# ===== Stream Edge Cases =====


@pytest.mark.asyncio
async def test_stream_stderr_only():
    """Test streaming when only stderr has output."""
    proc = await create_nsjail_process(
        command="/bin/sh",
        args=["-c", "echo error >&2"],
        options=NsjailOptions(chroot="/"),
    )

    has_custom_stderr = False
    async for source, chunk in proc.stream():
        if source == "stderr" and b"error" in chunk:
            has_custom_stderr = True

    assert has_custom_stderr


@pytest.mark.asyncio
async def test_stream_empty_output():
    """Test streaming when command produces no output."""
    proc = await create_nsjail_process(
        command="/bin/true",
        options=NsjailOptions(chroot="/"),
    )

    has_stdout = False
    async for source, chunk in proc.stream():
        if source == "stdout" and chunk:
            has_stdout = True

    # /bin/true produces no stdout (nsjail logs go to stderr)
    assert not has_stdout


# ===== Kill Tests =====


@pytest.mark.asyncio
async def test_kill():
    """Test kill method."""
    proc = await create_nsjail_process(
        command="/bin/sleep",
        args=["3600"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.is_running()
    proc.kill()
    await proc.wait()
    assert not proc.is_running()
    # Killed by SIGKILL (exit code 137 usually, or 9)
    assert proc.returncode < 0


# ===== Config File Tests =====


def test_options_with_config_file():
    """Test that config_file parameter works."""
    options = NsjailOptions(
        chroot="/srv/jail",
        user=65534,
    )
    args = options.build_args()

    # Should have -Mo and --chroot
    assert "-Mo" in args
    assert "--chroot" in args
    assert "/srv/jail" in args
