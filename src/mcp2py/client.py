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

    def __init__(
        self,
        command: list[str],
        roots: list[dict[str, str]] | None = None,
        sampling_callback: Any | None = None,
        elicitation_callback: Any | None = None,
    ) -> None:
        """Initialize MCP client wrapper.

        Args:
            command: Command and arguments to launch the MCP server
            roots: Optional list of root directories to expose to server
            sampling_callback: Optional callback for sampling requests
            elicitation_callback: Optional callback for elicitation requests

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
        self._roots = roots or []
        self._sampling_callback = sampling_callback
        self._elicitation_callback = elicitation_callback

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
                # Create roots callback if roots are provided
                list_roots_callback = None
                if self._roots:

                    async def roots_callback(request=None):
                        """Return the configured roots."""
                        from mcp.types import Root, ListRootsResult

                        roots = [
                            Root(uri=r["uri"], name=r.get("name", ""))
                            for r in self._roots
                        ]
                        return ListRootsResult(roots=roots)

                    list_roots_callback = roots_callback

                async with ClientSession(
                    read,
                    write,
                    list_roots_callback=list_roots_callback,
                    sampling_callback=self._sampling_callback,
                    elicitation_callback=self._elicitation_callback,
                ) as session:
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

        Performs the MCP initialization handshake. Roots are declared via
        the session's list_roots_callback, not during initialization.

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

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources from the server.

        Returns:
            List of resource schemas with uri, name, description, mimeType

        Raises:
            RuntimeError: If not initialized or request fails

        Example:
            >>> resources = await client.list_resources()
            >>> isinstance(resources, list)
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's list_resources method
        response = await self._session.list_resources()

        # Convert to compatible format
        resources: list[dict[str, Any]] = [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description or "",
                "mimeType": resource.mimeType if hasattr(resource, "mimeType") else None,
            }
            for resource in response.resources
        ]

        return resources

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource by URI.

        Args:
            uri: URI of the resource to read

        Returns:
            Resource content

        Raises:
            RuntimeError: If not initialized or read fails

        Example:
            >>> result = await client.read_resource("file:///docs")
            >>> "contents" in result
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's read_resource method
        response = await self._session.read_resource(uri)

        # Convert to compatible format
        contents = [
            {
                "uri": item.uri,
                "mimeType": item.mimeType if hasattr(item, "mimeType") else None,
                "text": item.text if hasattr(item, "text") else None,
                "blob": item.blob if hasattr(item, "blob") else None,
            }
            for item in response.contents
        ]

        return {"contents": contents}

    async def list_prompts(self) -> list[dict[str, Any]]:
        """List available prompts from the server.

        Returns:
            List of prompt schemas with name, description, arguments

        Raises:
            RuntimeError: If not initialized or request fails

        Example:
            >>> prompts = await client.list_prompts()
            >>> isinstance(prompts, list)
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's list_prompts method
        response = await self._session.list_prompts()

        # Convert to compatible format
        prompts: list[dict[str, Any]] = [
            {
                "name": prompt.name,
                "description": prompt.description or "",
                "arguments": [
                    {
                        "name": arg.name,
                        "description": arg.description or "",
                        "required": arg.required if hasattr(arg, "required") else False,
                    }
                    for arg in (prompt.arguments or [])
                ],
            }
            for prompt in response.prompts
        ]

        return prompts

    async def get_prompt(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get a prompt with arguments.

        Args:
            name: Name of the prompt
            arguments: Arguments for the prompt

        Returns:
            Prompt result with messages

        Raises:
            RuntimeError: If not initialized or request fails

        Example:
            >>> result = await client.get_prompt("review_code", {"code": "def foo(): pass"})
            >>> "messages" in result
            True
        """
        if not self._initialized or self._session is None:
            raise RuntimeError("Not initialized - call initialize() first")

        # Use official SDK's get_prompt method
        response = await self._session.get_prompt(name, arguments or {})

        # Convert to compatible format
        messages = [
            {
                "role": msg.role,
                "content": msg.content.model_dump()
                if hasattr(msg.content, "model_dump")
                else str(msg.content),
            }
            for msg in response.messages
        ]

        return {"messages": messages}

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
