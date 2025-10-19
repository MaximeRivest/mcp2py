"""Event loop runner for sync API over async implementation.

This module provides AsyncRunner, which creates a background event loop thread
for running async operations synchronously. Works in both normal Python and
Jupyter environments.
"""

import asyncio
import threading
from typing import Any, Coroutine, TypeVar

T = TypeVar("T")


def _apply_nest_asyncio_if_needed() -> None:
    """Apply nest_asyncio patch if in Jupyter/IPython environment.

    This allows nested event loops, which is needed for VS Code Jupyter.
    """
    try:
        # Check if we're in Jupyter/IPython
        get_ipython()  # type: ignore

        # We're in IPython, apply nest_asyncio
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            # nest_asyncio not available, continue without it
            pass
    except NameError:
        # Not in IPython, no need for nest_asyncio
        pass


class AsyncRunner:
    """Async runner with background event loop thread.

    Always creates a dedicated background thread with its own event loop,
    regardless of whether another loop is running. This approach:
    - Works in normal Python environments
    - Works in Jupyter/IPython (applies nest_asyncio if available)
    - Keeps subprocess stdio in the background thread (important for VS Code)

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
        self._closed = False

        # Apply nest_asyncio if in Jupyter environment
        _apply_nest_asyncio_if_needed()

        self._start_background_loop()

    def _start_background_loop(self) -> None:
        """Start background event loop in thread."""
        started = threading.Event()

        def run_loop() -> None:
            # Create new event loop for this thread
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            started.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        started.wait()  # Wait for loop to be ready

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        """Run coroutine in background loop, return result synchronously.

        Args:
            coro: Coroutine to execute

        Returns:
            Result from the coroutine

        Raises:
            RuntimeError: If event loop is not available
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

        # Submit to background thread and wait for result
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
