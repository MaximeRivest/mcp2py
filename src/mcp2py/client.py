"""MCP client wrapper around official SDK.

This module provides a wrapper around the official MCP Python SDK's ClientSession,
maintaining the same interface as our previous custom implementation while using
the battle-tested official SDK under the hood.
"""

import asyncio
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Wrapper around official MCP SDK's ClientSession.

    Provides the same interface as our previous custom implementation,
    but delegates to the official SDK for protocol handling.

    This implementation maintains the stdio and session contexts as long-running
    background tasks to ensure the subprocess and connections stay alive.

    Example:
        >>> client = MCPClient(["python", "server.py"])
        >>> await client.connect()
        >>> await client.initialize({"name": "mcp2py", "version": "0.1.0"})
        >>> tools = await client.list_tools()
        >>> result = await client.call_tool("echo", {"message": "hello"})
        >>> await client.close()
    """

    def __init__(self, command: list[str]) -> None:
        """Initialize MCP client wrapper.

        Args:
            command: Command and arguments to launch the MCP server

        Example:
            >>> client = MCPClient(["npx", "weather-server"])
        """
        # Parse command into server parameters
        if not command:
            raise ValueError("Command cannot be empty")

        self.server_params = StdioServerParameters(
            command=command[0],
            args=command[1:] if len(command) > 1 else [],
            env=None
        )

        # Session will be set during connect()
        self._session: ClientSession | None = None
        self._initialized = False

        # Context manager task and events
        self._context_task: asyncio.Task[None] | None = None
        self._ready_event: asyncio.Event | None = None
        self._shutdown_event: asyncio.Event | None = None
        self._connection_error: Exception | None = None

    async def connect(self) -> None:
        """Connect to MCP server via stdio transport.

        Creates a ClientSession that will be used for all subsequent operations.

        Raises:
            RuntimeError: If connection fails

        Example:
            >>> await client.connect()
        """
        # Get the current event loop (will be the AsyncRunner's background loop)
        loop = asyncio.get_running_loop()

        # Create events for coordination
        self._ready_event = asyncio.Event()
        self._shutdown_event = asyncio.Event()
        self._connection_error = None

        # Start context manager task in the current (background) loop
        self._context_task = loop.create_task(self._run_contexts())

        # Wait for connection to be ready (or error)
        await self._ready_event.wait()

        # Check if connection failed
        if self._connection_error:
            cmd = f"{self.server_params.command} {' '.join(self.server_params.args)}"
            raise RuntimeError(
                f"Failed to connect to MCP server '{cmd}': {self._connection_error}\n\n"
                f"This could be caused by:\n"
                f"  - Server executable not found or not executable\n"
                f"  - Server crashing during startup\n"
                f"  - Missing dependencies or configuration\n"
                f"  - In Jupyter: try restarting the kernel\n\n"
                f"Try running the command manually to diagnose:\n"
                f"  $ {cmd}"
            ) from self._connection_error

        if self._session is None:
            raise RuntimeError("Failed to establish session - unknown error")

    async def _run_contexts(self) -> None:
        """Run the stdio and session contexts as a long-lived task.

        This keeps the subprocess and connections alive throughout the session.
        """
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    self._session = session

                    # Signal that we're ready (connection successful)
                    if self._ready_event:
                        self._ready_event.set()

                    # Keep contexts alive until shutdown
                    if self._shutdown_event:
                        await self._shutdown_event.wait()
        except Exception as e:
            # Store error for connect() to retrieve
            self._connection_error = e

            # Signal ready so connect() can proceed and raise the error
            if self._ready_event:
                self._ready_event.set()

            # Don't re-raise here - let connect() handle it
        finally:
            self._session = None

    async def initialize(self, client_info: dict[str, str]) -> dict[str, Any]:
        """Initialize MCP session with the server.

        Performs the MCP initialization handshake.

        Args:
            client_info: Client information (name, version)

        Returns:
            Server initialization response with capabilities

        Raises:
            RuntimeError: If not connected or initialization fails

        Example:
            >>> info = {"name": "mcp2py", "version": "0.1.0"}
            >>> response = await client.initialize(client_info=info)
            >>> "capabilities" in response
            True
        """
        if self._session is None:
            raise RuntimeError("Not connected - call connect() first")

        # Use official SDK's initialize method
        response = await self._session.initialize()

        self._initialized = True

        # Return server info in compatible format
        return {
            "capabilities": response.capabilities.model_dump()
            if hasattr(response.capabilities, "model_dump")
            else {},
            "serverInfo": response.serverInfo.model_dump()
            if hasattr(response, "serverInfo") and hasattr(response.serverInfo, "model_dump")
            else {},
        }

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from the server.

        Returns:
            List of tool schemas with name, description, and inputSchema

        Raises:
            RuntimeError: If not initialized or request fails

        Example:
            >>> tools = await client.list_tools()
            >>> isinstance(tools, list)
            True
            >>> all("name" in tool for tool in tools)
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's list_tools method
        response = await self._session.list_tools()

        # Convert to compatible format
        tools: list[dict[str, Any]] = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        return tools

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Call a tool and return result.

        Args:
            name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool execution result with content

        Raises:
            RuntimeError: If not initialized or tool call fails

        Example:
            >>> result = await client.call_tool("echo", {"message": "hello"})
            >>> "content" in result
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's call_tool method
        response = await self._session.call_tool(name, arguments)

        # Convert to compatible format
        content = [
            {
                "type": item.type,
                "text": item.text if hasattr(item, "text") else str(item),
            }
            for item in response.content
        ]

        return {"content": content}

    async def close(self) -> None:
        """Close the connection and cleanup resources.

        Example:
            >>> await client.close()
        """
        # Signal shutdown to context task
        if self._shutdown_event:
            self._shutdown_event.set()

        # Wait for context task to complete
        if self._context_task:
            try:
                await asyncio.wait_for(self._context_task, timeout=5.0)
            except asyncio.TimeoutError:
                # Force cancel if it doesn't shut down gracefully
                self._context_task.cancel()
                try:
                    await self._context_task
                except asyncio.CancelledError:
                    pass
            except Exception:
                pass

        self._session = None
        self._initialized = False
        self._context_task = None
        self._ready_event = None
        self._shutdown_event = None
