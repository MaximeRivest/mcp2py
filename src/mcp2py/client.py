"""MCP client wrapper around official SDK.

This module provides a wrapper around the official MCP Python SDK's ClientSession,
maintaining the same interface as our previous custom implementation while using
the battle-tested official SDK under the hood.
"""

from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Wrapper around official MCP SDK's ClientSession.

    Provides the same interface as our previous custom implementation,
    but delegates to the official SDK for protocol handling.

    Note: This class uses context managers internally. The connect() and close()
    methods manage the lifecycle of the underlying stdio_client and ClientSession.

    Example:
        >>> client = MCPClient([" python", "server.py"])
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

        # Keep references to the read/write streams
        self._read: Any = None
        self._write: Any = None

    async def connect(self) -> None:
        """Connect to MCP server via stdio transport.

        Creates a ClientSession that will be used for all subsequent operations.

        Raises:
            RuntimeError: If connection fails

        Example:
            >>> await client.connect()
        """
        # Create stdio connection and get read/write streams
        # We need to keep the context alive, so we don't use "async with" here
        from mcp.client.stdio import stdio_client as _stdio_client_func

        # Create the stdio connection
        self._stdio_manager = _stdio_client_func(self.server_params)
        self._read, self._write = await self._stdio_manager.__aenter__()

        # Create and enter client session context
        self._session_manager = ClientSession(self._read, self._write)
        self._session = await self._session_manager.__aenter__()

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
        # Exit contexts in reverse order
        if hasattr(self, '_session_manager') and self._session_manager:
            try:
                await self._session_manager.__aexit__(None, None, None)
            except Exception:
                pass

        if hasattr(self, '_stdio_manager') and self._stdio_manager:
            try:
                await self._stdio_manager.__aexit__(None, None, None)
            except Exception:
                pass

        self._session = None
        self._initialized = False
