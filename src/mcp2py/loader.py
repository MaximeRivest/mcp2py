"""Loader for MCP servers.

This module provides the main entry point for loading MCP servers and
creating Python interfaces to them.
"""

from typing import Any

from mcp2py.client import MCPClient
from mcp2py.event_loop import AsyncRunner
from mcp2py.schema import parse_command
from mcp2py.server import MCPServer


def load(command: str | list[str], **kwargs: Any) -> MCPServer:
    """Load MCP server and return Python interface.

    Launches the server subprocess, connects via stdio, performs MCP
    initialization handshake, and returns a synchronous Python interface
    with tools as methods.

    Args:
        command: Command to launch server (e.g., "npx weather-server",
                 "python server.py", or pre-split list)
        **kwargs: Reserved for future options (auth, sampling, etc.)

    Returns:
        MCPServer object with tools as methods

    Raises:
        RuntimeError: If connection or initialization fails
        ValueError: If command is invalid

    Example:
        >>> server = load("python tests/test_server.py")
        >>> result = server.echo(message="Hello!")
        >>> "Hello!" in result
        True
        >>> server.close()

    Example with context manager:
        >>> with load("python tests/test_server.py") as server:
        ...     result = server.echo(message="test")
        ...     "test" in result
        True

    Example with list command:
        >>> server = load(["python", "tests/test_server.py"])
        >>> result = server.add(a=5, b=3)
        >>> "8" in result
        True
        >>> server.close()
    """
    # Parse command into list
    cmd_list = parse_command(command)

    if not cmd_list:
        raise ValueError("Command cannot be empty")

    # Create async runner (background event loop in thread)
    runner = AsyncRunner()

    # Create MCP client
    client = MCPClient(cmd_list)

    # Connect and initialize synchronously via runner
    try:
        # Connect to server subprocess
        runner.run(client.connect())

        # MCP initialization handshake
        runner.run(
            client.initialize(
                client_info={
                    "name": "mcp2py",
                    "version": "0.1.0",
                }
            )
        )

        # List available tools
        tools = runner.run(client.list_tools())

    except Exception as e:
        # Cleanup on failure
        try:
            runner.close()
        except Exception:
            pass

        raise RuntimeError(f"Failed to connect to MCP server: {e}") from e

    # Return synchronous wrapper
    return MCPServer(client, runner, tools)
