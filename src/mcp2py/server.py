"""MCPServer wrapper providing Pythonic interface to MCP tools.

This module provides the MCPServer class which wraps an MCPClient and exposes
tools as Python methods with automatic name conversion and result unwrapping.
"""

from typing import Any

from mcp2py.client import MCPClient
from mcp2py.event_loop import AsyncRunner
from mcp2py.schema import camel_to_snake


class MCPServer:
    """Pythonic wrapper around MCP client.

    Exposes MCP tools as Python methods, handling async execution via
    background event loop and providing clean synchronous API.

    Example:
        >>> # Typically created via load(), not directly
        >>> from mcp2py import load
        >>> server = load("python tests/test_server.py")
        >>> result = server.echo(message="Hello!")
        >>> "Hello!" in result
        True
        >>> server.close()
    """

    def __init__(
        self,
        client: MCPClient,
        runner: AsyncRunner,
        tools: list[dict[str, Any]],
    ) -> None:
        """Initialize MCP server wrapper.

        Args:
            client: Connected MCPClient instance
            runner: AsyncRunner for sync/async bridge
            tools: List of tool schemas from server
        """
        self._client = client
        self._runner = runner
        self._tools = {tool["name"]: tool for tool in tools}

        # Create bidirectional mapping: snake_case <-> original
        self._name_map: dict[str, str] = {}
        for original_name in self._tools.keys():
            snake_name = camel_to_snake(original_name)
            # Only map if different (don't override already snake_case names)
            if snake_name != original_name:
                self._name_map[snake_name] = original_name

    def __getattr__(self, name: str) -> Any:
        """Dynamically create tool methods.

        Args:
            name: Tool name (snake_case or original)

        Returns:
            Callable that executes the tool

        Raises:
            AttributeError: If tool not found

        Example:
            >>> server = load("python tests/test_server.py")
            >>> echo_func = server.echo
            >>> callable(echo_func)
            True
            >>> server.close()
        """
        # Try snake_case mapping first
        original_name = self._name_map.get(name)

        # If not in mapping, try exact match
        if original_name is None:
            if name not in self._tools:
                available = sorted(
                    set(list(self._name_map.keys()) + list(self._tools.keys()))
                )
                raise AttributeError(
                    f"Tool '{name}' not found. Available tools: {', '.join(available)}"
                )
            original_name = name

        tool_schema = self._tools[original_name]

        # Return callable that executes the tool
        def tool_method(**kwargs: Any) -> Any:
            result = self._runner.run(self._client.call_tool(original_name, kwargs))
            return self._unwrap_result(result)

        # Set metadata
        tool_method.__name__ = name
        tool_method.__doc__ = tool_schema.get("description", "")

        return tool_method

    def _unwrap_result(self, result: dict[str, Any]) -> Any:
        """Extract content from MCP response.

        Args:
            result: Raw MCP tool call result

        Returns:
            Unwrapped content (string if single text, list otherwise)

        Example:
            >>> server = load("python tests/test_server.py")
            >>> # Results are automatically unwrapped
            >>> result = server.echo(message="test")
            >>> isinstance(result, str)
            True
            >>> server.close()
        """
        content = result.get("content", [])

        # If single text response, return just the text
        if len(content) == 1 and content[0].get("type") == "text":
            return content[0]["text"]

        # Otherwise return full content list
        return content

    def close(self) -> None:
        """Close connection and cleanup resources.

        Terminates the server subprocess and stops the background event loop.

        Example:
            >>> server = load("python tests/test_server.py")
            >>> server.close()
        """
        if not hasattr(self, "_closed"):
            self._closed = False

        if self._closed:
            return

        self._closed = True

        # Close client connection (stops subprocess)
        try:
            self._runner.run(self._client.close())
        except Exception:
            pass

        # Stop event loop
        try:
            self._runner.close()
        except Exception:
            pass

    def __enter__(self) -> "MCPServer":
        """Enter context manager.

        Example:
            >>> with load("python tests/test_server.py") as server:
            ...     result = server.echo(message="test")
            ...     "test" in result
            True
        """
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and cleanup.

        Example:
            >>> with load("python tests/test_server.py") as server:
            ...     pass
            ... # Automatically closed
        """
        self.close()

    def __del__(self) -> None:
        """Safety net cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass
