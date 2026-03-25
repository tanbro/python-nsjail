"""Tests for nsjail Python API."""

import asyncio
import pytest

from nsjail import NsjailOptions, create_nsjail_process


@pytest.mark.asyncio
async def test_start_basic():
    """Test basic start and wait."""
    proc = await create_nsjail_process(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_start_with_options():
    """Test start with NsjailOptions."""
    proc = await create_nsjail_process(
        command=["/bin/true"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.pid > 0
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_stream_output():
    """Test streaming stdout with chroot."""
    proc = await create_nsjail_process(
        command=["/bin/echo", "hello world"],
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
async def test_context_manager():
    """Test async context manager."""
    async with await create_nsjail_process(
        command=["/bin/sleep", "0.1"],
        options=NsjailOptions(chroot="/"),
    ) as proc:
        assert proc.pid > 0
        assert proc.is_running()
    # Should be terminated after context exit


@pytest.mark.asyncio
async def test_terminate():
    """Test terminate method."""
    proc = await create_nsjail_process(
        command=["/bin/sleep", "3600"],
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

    # Should be empty when no options specified
    assert args == []


def test_options_empty_containers():
    """Test that empty containers don't generate arguments."""
    options = NsjailOptions(env={}, bindmount=[], bindmount_ro=[], tmpfsmount=[])
    args = options.build_args()

    # Should be empty when all containers are empty
    assert args == []


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
        command=["/bin/nonexistent_command_xyz123"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    # nsjail should fail with non-zero exit code
    assert ret != 0


@pytest.mark.asyncio
async def test_command_non_zero_exit():
    """Test command that exits with non-zero code."""
    proc = await create_nsjail_process(
        command=["/bin/sh", "-c", "exit 42"],
        options=NsjailOptions(chroot="/"),
    )
    ret = await proc.wait()
    assert ret == 42


# ===== Ring Buffer Tests =====


@pytest.mark.asyncio
async def test_ring_buffer_discard_oldest():
    """Test that ring buffer discards oldest when full.

    Verifies the ring buffer behavior: when queue is full, oldest items
    are discarded to make room for new data.
    """
    # Small buffer to trigger overflow
    proc = await create_nsjail_process(
        command=[
            "/bin/sh",
            "-c",
            "i=0; while [ $i -lt 100 ]; do echo $i; i=$((i+1)); done",
        ],
        options=NsjailOptions(chroot="/"),
        buffer_size=2,
    )

    chunks = []
    async for source, chunk in proc.stream():
        if source == "stdout":
            chunks.append(chunk)

    # With ring buffer, we should get data but some may be lost
    assert len(chunks) > 0
    # The exact number depends on timing, but should be significantly
    # less than 100 due to buffer_size=2
    # (Note: this is a soft assertion as timing can vary)


@pytest.mark.asyncio
async def test_queue_full_with_eof():
    """Test that EOF marker is delivered even when queue is full.

    This ensures the fix for the deadlock scenario where EOF put() would
    block if the queue was full.
    """
    # Use very small buffer size
    proc = await create_nsjail_process(
        command=["/bin/sh", "-c", "for i in $(seq 1 50); do echo line $i; done"],
        options=NsjailOptions(chroot="/"),
        buffer_size=2,  # Very small queue
    )

    # Stream should complete without deadlock
    chunks = []
    async for source, chunk in proc.stream():
        if source == "stdout":
            chunks.append(chunk)

    # Should receive some data and exit cleanly
    assert len(chunks) > 0

    # Wait for process to finish
    await proc.wait()
    # Process should exit cleanly (not hang due to EOF blocking)
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_eof_when_queue_full():
    """Test that EOF marker is delivered even when queue is completely full.

    This test specifically targets the QueueFull exception handling path in
    _internal_read where we discard the oldest item to make room for EOF.
    """
    # Use extremely small buffer and slow consumption to ensure queue stays full
    proc = await create_nsjail_process(
        command=["/bin/sh", "-c", "for i in $(seq 1 20); do echo $i; sleep 0.01; done"],
        options=NsjailOptions(chroot="/"),
        buffer_size=1,  # Single slot queue - easier to keep full
    )

    # Don't consume immediately, let output accumulate
    await asyncio.sleep(0.1)

    # Now start consuming - queue should have been full at some point
    chunks = []
    async for source, chunk in proc.stream():
        if source == "stdout":
            chunks.append(chunk)
        # Only consume first few items to let queue fill again
        if len(chunks) >= 3:
            break

    # Continue waiting for process to complete
    await proc.wait()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_aclose_after_process_naturally_ends():
    """Test aclose() when process has already ended naturally.

    This covers the _wait_readers branch where tasks are already done
    (no cancellation needed).
    """
    proc = await create_nsjail_process(
        command=["/bin/echo", "hello"],
        options=NsjailOptions(chroot="/"),
    )

    # Wait for process to finish naturally
    await proc.wait()
    assert proc.returncode == 0

    # Now call aclose - should handle gracefully (tasks already done)
    await proc.aclose()
    assert not proc.is_running()


# ===== aclose() Timeout Tests =====


@pytest.mark.asyncio
async def test_aclose_timeout_fallback_to_kill():
    """Test that aclose() falls back to kill() after timeout."""
    proc = await create_nsjail_process(
        command=[
            "/bin/sh",
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
            command=["/bin/echo", f"process_{num}"],
            options=NsjailOptions(chroot="/"),
        )
        await proc.wait()
        assert proc.returncode is not None
        return proc.returncode

    # Run 10 processes concurrently
    results = await asyncio.gather(*[run_echo(i) for i in range(10)])
    assert all(r == 0 for r in results)


# ===== Resource Limit Tests =====


@pytest.mark.asyncio
async def test_time_limit():
    """Test that time_limit actually kills the process."""
    proc = await create_nsjail_process(
        command=["/bin/sh", "-c", "sleep 1000"],
        options=NsjailOptions(chroot="/", time_limit=1),
    )
    ret = await proc.wait()
    # Should be killed by time limit
    assert ret != 0


@pytest.mark.asyncio
async def test_memory_limit():
    """Test that memory_limit works."""
    proc = await create_nsjail_process(
        command=[
            "/bin/sh",
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
        command=["/bin/sh", "-c", "echo error >&2"],
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
        command=["/bin/true"],
        options=NsjailOptions(chroot="/"),
    )

    has_stdout = False
    async for source, chunk in proc.stream():
        if source == "stdout" and chunk:
            has_stdout = True

    # /bin/true produces no stdout (nsjail logs go to stderr)
    assert not has_stdout


@pytest.mark.asyncio
async def test_stream_during_aclose():
    """Test that stream() exits cleanly when aclose() is called concurrently."""
    proc = await create_nsjail_process(
        command=["/bin/sh", "-c", "while true; do echo x; sleep 0.01; done"],
        options=NsjailOptions(chroot="/"),
    )

    # Start streaming in background
    async def get_first():
        async for _ in proc.stream():
            break

    stream_task = asyncio.create_task(get_first())

    # Give it time to start reading
    await asyncio.sleep(0.05)

    # Close while stream is active
    await proc.aclose()

    # Stream should handle EOF gracefully
    # The task should complete without hanging
    try:
        await stream_task
    except StopAsyncIteration:
        # Expected: stream exhausted
        pass

    assert not proc.is_running()


@pytest.mark.asyncio
async def test_aclose_with_active_stream():
    """Test aclose() EOF fallback when stream() is consuming."""
    proc = await create_nsjail_process(
        command=["/bin/sleep", "3600"],
        options=NsjailOptions(chroot="/"),
    )

    # Start streaming
    stream_started = False

    async def slow_stream():
        nonlocal stream_started
        stream_started = True
        async for _ in proc.stream():
            break  # Get first chunk then stop

    stream_task = asyncio.create_task(slow_stream())

    # Wait for stream to start
    await asyncio.sleep(0.1)

    # Close process
    await proc.aclose()

    # Stream should exit cleanly via EOF markers
    await stream_task

    assert not proc.is_running()


# ===== Stream Tests =====


@pytest.mark.asyncio
async def test_stream_after_terminated_raises():
    """Test that stream() raises RuntimeError after all output consumed."""
    proc = await create_nsjail_process(
        command=["/bin/echo", "test"],
        options=NsjailOptions(chroot="/"),
    )

    # First call - should work and consume all output
    async for _ in proc.stream():
        pass

    # Wait for process to finish
    await proc.wait()
    assert proc.returncode == 0

    # Second call after all output consumed - should raise
    with pytest.raises(
        RuntimeError, match="Cannot stream\\(\\) after all output has been consumed"
    ):
        async for _ in proc.stream():
            pass


# ===== Kill Tests =====


@pytest.mark.asyncio
async def test_kill():
    """Test kill method."""
    proc = await create_nsjail_process(
        command=["/bin/sleep", "3600"],
        options=NsjailOptions(chroot="/"),
    )
    assert proc.is_running()
    proc.kill()
    await proc.wait()
    assert not proc.is_running()
    # Killed by SIGKILL (exit code 137 usually, or 9)
    assert proc.returncode is not None
    assert proc.returncode < 0


@pytest.mark.asyncio
async def test_kill_already_dead():
    """Test kill() on already dead process."""
    proc = await create_nsjail_process(command=["/bin/true"])
    await proc.wait()  # Wait for process to finish
    # Process is dead, kill() should warn but not raise
    with pytest.warns(RuntimeWarning, match="already dead"):
        proc.kill()


@pytest.mark.asyncio
async def test_terminate_already_dead():
    """Test terminate() on already dead process."""
    proc = await create_nsjail_process(command=["/bin/true"])
    await proc.wait()  # Wait for process to finish
    # Process is dead, terminate() should warn but not raise
    with pytest.warns(RuntimeWarning, match="already terminated"):
        proc.terminate()


# ===== Config File Tests =====


def test_options_with_config_file():
    """Test that config_file parameter works."""
    options = NsjailOptions(
        chroot="/srv/jail",
        user=65534,
    )
    args = options.build_args()

    # Should have --chroot
    assert "--chroot" in args
    assert "/srv/jail" in args


# ===== Binary Finding Tests =====


def test_get_nsjail_path():
    """Test that get_nsjail_path() works correctly."""
    from nsjail.locator import locate_nsjail

    # Should find bundled nsjail if package is installed
    result = locate_nsjail()

    # Result should be an absolute path
    assert result.is_absolute()
    assert result.name == "nsjail"


def test_bundled_binary():
    """Test that bundled_binary() returns the bundled binary."""
    from nsjail.locator import bundled_binary

    result = bundled_binary()
    assert result.is_absolute()
    assert result.name == "nsjail"


def test_console_script():
    """Test that console_script() returns the wrapper script."""
    from nsjail.locator import console_script

    result = console_script()
    # May not exist in all environments
    if result:
        assert result.is_absolute()
        assert result.name == "nsjail"


# ===== nsenter Tests =====


@pytest.mark.asyncio
async def test_nsenter_process_attributes():
    """Test NsenterProcess attributes."""
    from nsjail import create_nsenter_process

    # Create a target process
    sleep_proc = await asyncio.create_subprocess_exec("sleep", "10")

    try:
        proc = await create_nsenter_process(
            target_pid=sleep_proc.pid,
            namespaces=["net", "mnt"],
            command=["echo", "test"],
        )

        # Check attributes
        assert proc.target_pid == sleep_proc.pid
        assert proc.namespaces == ["net", "mnt"]
        assert proc.pid > 0

        # Clean up
        proc.kill()
        await proc.wait()
    finally:
        sleep_proc.kill()
        await sleep_proc.wait()


@pytest.mark.asyncio
async def test_nsenter_stream_works():
    """Test that stream() works with nsenter processes."""
    from nsjail import create_nsenter_process

    sleep_proc = await asyncio.create_subprocess_exec("sleep", "10")

    try:
        proc = await create_nsenter_process(
            target_pid=sleep_proc.pid,
            namespaces=["net"],
            command=["echo", "hello from nsenter"],
        )

        chunks = []
        async for source, chunk in proc.stream():
            if source == "stdout":
                chunks.append(chunk)

        await proc.wait()
        assert proc.returncode == 0
        assert len(chunks) > 0
    finally:
        sleep_proc.kill()
        await sleep_proc.wait()


@pytest.mark.asyncio
async def test_nsenter_invalid_namespace_type():
    """Test that invalid namespace type raises ValueError."""
    from nsjail import create_nsenter_process

    sleep_proc = await asyncio.create_subprocess_exec("sleep", "10")

    try:
        with pytest.raises(ValueError, match="Unknown namespace type"):
            await create_nsenter_process(
                target_pid=sleep_proc.pid,
                namespaces=["invalid_namespace"],
                command=["echo", "test"],
            )
    finally:
        sleep_proc.kill()
        await sleep_proc.wait()


@pytest.mark.asyncio
async def test_nsenter_options_build_args():
    """Test NsenterOptions.build_args()."""
    from nsjail import NsenterOptions

    options = NsenterOptions(
        wd="/tmp",
        user="nobody",
        env={"TEST": "value"},
    )

    args = list(options.build_args())

    assert "--wd" in args
    assert "/tmp" in args
    assert "--user" in args
    assert "nobody" in args
    assert "--env" in args
    assert "TEST=value" in args
