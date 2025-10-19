"""Background event loop runner for sync API over async implementation.

This module provides AsyncRunner, which manages a background event loop in a separate
thread, allowing synchronous code to call async functions seamlessly.
"""

import asyncio
import threading
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


class AsyncRunner:
    """Thread-safe async runner with background event loop.

    Creates and manages an event loop in a background thread, allowing
    synchronous code to execute async coroutines and get results.

    Example:
        >>> runner = AsyncRunner()
        >>> async def get_value():
        ...     return 42
        >>> result = runner.run(get_value())
        >>> result
        42
        >>> runner.close()
    """

    def __init__(self) -> None:
        """Initialize and start background event loop."""
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._closed = False
        self._start()

    def _start(self) -> None:
        """Start background event loop in thread."""

        def run_loop() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._started.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        self._started.wait()  # Wait for loop to be ready

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run coroutine in background loop, return result synchronously.

        Args:
            coro: Coroutine to execute

        Returns:
            Result from the coroutine

        Raises:
            RuntimeError: If event loop is not started or closed
            Exception: Any exception raised by the coroutine

        Example:
            >>> runner = AsyncRunner()
            >>> async def add(a, b):
            ...     return a + b
            >>> runner.run(add(2, 3))
            5
            >>> runner.close()
        """
        if self._loop is None or self._closed:
            raise RuntimeError("Event loop not available")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()  # Blocks until complete

    def close(self) -> None:
        """Stop event loop and cleanup resources.

        Example:
            >>> runner = AsyncRunner()
            >>> runner.close()
        """
        if self._closed:
            return

        self._closed = True

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread:
            self._thread.join(timeout=5.0)

    def __enter__(self) -> "AsyncRunner":
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and cleanup."""
        self.close()

    def __del__(self) -> None:
        """Cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass
