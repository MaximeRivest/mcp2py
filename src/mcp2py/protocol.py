"""Low-level MCP protocol client.

Handles:
- Initialize handshake
- Capability negotiation
- Request/response correlation
- Error handling
"""

from typing import Any

from mcp2py.transport import StdioTransport


class MCPClient:
    """Low-level MCP protocol client.

    Handles the MCP protocol handshake, tool management, and execution.

    Example:
        >>> transport = StdioTransport(["npx", "server"])
        >>> client = MCPClient(transport)
        >>> await client.initialize(client_info={"name": "mcp2py"})
        >>> tools = await client.list_tools()
        >>> len(tools) > 0
        True
    """

    def __init__(self, transport: StdioTransport) -> None:
        """Initialize MCP client with a transport.

        Args:
            transport: Transport layer for JSON-RPC communication

        Example:
            >>> transport = StdioTransport(["python", "server.py"])
            >>> client = MCPClient(transport)
        """
        self.transport = transport
        self._next_id = 1
        self._initialized = False

    async def initialize(self, client_info: dict[str, str]) -> dict[str, Any]:
        """Initialize MCP session with the server.

        Performs the MCP initialization handshake:
        1. Sends initialize request
        2. Waits for server capabilities response
        3. Sends initialized notification

        Args:
            client_info: Client information (name, version)

        Returns:
            Server initialization response with capabilities

        Raises:
            RuntimeError: If initialization fails

        Example:
            >>> info = {"name": "mcp2py", "version": "0.1.0"}
            >>> response = await client.initialize(client_info=info)
            >>> "capabilities" in response
            True
        """
        # Send initialize request
        init_response = await self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": client_info
            }
        )

        # Verify we got a valid response
        if "result" not in init_response:
            error = init_response.get("error", {})
            raise RuntimeError(
                f"Initialize failed: {error.get('message', 'Unknown error')}"
            )

        # Send initialized notification (no response expected)
        await self.transport.send({
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })

        self._initialized = True
        result: dict[str, Any] = init_response["result"]
        return result

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
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")

        response = await self._request("tools/list", {})

        if "result" not in response:
            error = response.get("error", {})
            raise RuntimeError(
                f"tools/list failed: {error.get('message', 'Unknown error')}"
            )

        # Extract tools from result
        result = response["result"]
        tools: list[dict[str, Any]] = result.get("tools", [])
        return tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any]
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
        if not self._initialized:
            raise RuntimeError("Not initialized - call initialize() first")

        response = await self._request(
            "tools/call",
            {
                "name": name,
                "arguments": arguments
            }
        )

        if "result" not in response:
            error = response.get("error", {})
            raise RuntimeError(
                f"tools/call failed: {error.get('message', 'Unknown error')}"
            )

        # Return the full result
        result: dict[str, Any] = response["result"]
        return result

    async def _request(
        self,
        method: str,
        params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a JSON-RPC request and wait for response.

        Handles request ID generation and correlation.

        Args:
            method: JSON-RPC method name
            params: Method parameters

        Returns:
            JSON-RPC response message
        """
        request_id = self._next_id
        self._next_id += 1

        await self.transport.send({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        })

        response = await self.transport.receive()
        return response
