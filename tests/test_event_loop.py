"""Tests for AsyncRunner event loop manager."""

import asyncio

import pytest

from mcp2py.event_loop import AsyncRunner


def test_async_runner_executes_coroutine():
    """Test that AsyncRunner executes coroutines and returns results."""
    runner = AsyncRunner()

    async def get_value():
        return 42

    result = runner.run(get_value())
    assert result == 42

    runner.close()


def test_async_runner_executes_with_arguments():
    """Test executing coroutine with arguments."""
    runner = AsyncRunner()

    async def add(a, b):
        return a + b

    result = runner.run(add(5, 3))
    assert result == 8

    runner.close()


def test_async_runner_executes_async_sleep():
    """Test executing coroutine with async operations."""
    runner = AsyncRunner()

    async def delayed_value():
        await asyncio.sleep(0.01)
        return "done"

    result = runner.run(delayed_value())
    assert result == "done"

    runner.close()


def test_async_runner_handles_exceptions():
    """Test that exceptions from coroutines are propagated."""
    runner = AsyncRunner()

    async def raise_error():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        runner.run(raise_error())

    runner.close()


def test_async_runner_multiple_calls():
    """Test making multiple calls to the same runner."""
    runner = AsyncRunner()

    async def get_number(n):
        return n * 2

    assert runner.run(get_number(5)) == 10
    assert runner.run(get_number(10)) == 20
    assert runner.run(get_number(15)) == 30

    runner.close()


def test_async_runner_cleanup():
    """Test that cleanup stops the event loop."""
    runner = AsyncRunner()

    async def simple():
        return True

    result = runner.run(simple())
    assert result is True

    runner.close()

    # After close, should raise error
    with pytest.raises(RuntimeError, match="Event loop not available"):
        runner.run(simple())


def test_async_runner_context_manager():
    """Test AsyncRunner as context manager."""
    async def get_value():
        return 100

    with AsyncRunner() as runner:
        result = runner.run(get_value())
        assert result == 100

    # After context exit, should be closed
    with pytest.raises(RuntimeError, match="Event loop not available"):
        runner.run(get_value())


def test_async_runner_double_close():
    """Test that calling close() multiple times is safe."""
    runner = AsyncRunner()

    async def noop():
        pass

    runner.run(noop())
    runner.close()
    runner.close()  # Should not raise


def test_async_runner_concurrent_operations():
    """Test that runner can handle operations that spawn concurrent tasks."""
    runner = AsyncRunner()

    async def concurrent_operations():
        async def task(n):
            await asyncio.sleep(0.001)
            return n * 2

        # Run tasks concurrently
        results = await asyncio.gather(task(1), task(2), task(3))
        return sum(results)

    result = runner.run(concurrent_operations())
    assert result == 12  # (1*2) + (2*2) + (3*2)

    runner.close()


def test_async_runner_returns_none():
    """Test that runner correctly handles None returns."""
    runner = AsyncRunner()

    async def returns_none():
        return None

    result = runner.run(returns_none())
    assert result is None

    runner.close()


def test_async_runner_returns_complex_types():
    """Test that runner handles complex return types."""
    runner = AsyncRunner()

    async def returns_dict():
        return {"key": "value", "number": 42}

    result = runner.run(returns_dict())
    assert result == {"key": "value", "number": 42}

    async def returns_list():
        return [1, 2, 3, "four"]

    result = runner.run(returns_list())
    assert result == [1, 2, 3, "four"]

    runner.close()
