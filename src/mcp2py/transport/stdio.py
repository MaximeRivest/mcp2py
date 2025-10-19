"""Stdio transport for local MCP servers."""

import asyncio
import json
from typing import Any


class StdioTransport:
    """stdio-based transport for local MCP servers.

    Communicates with MCP servers via stdin/stdout using JSON-RPC.

    Example:
        >>> transport = StdioTransport(["npx", "-y", "mcp-server"])
        >>> await transport.connect()
        >>> await transport.send({"jsonrpc": "2.0", "method": "initialize"})
        >>> msg = await transport.receive()
        >>> await transport.close()
    """

    def __init__(self, command: list[str]) -> None:
        """Initialize stdio transport.

        Args:
            command: Command and arguments to launch the server

        Example:
            >>> transport = StdioTransport(["npx", "-y", "@h1deya/mcp-server-weather"])
        """
        self.command = command
        self.process: asyncio.subprocess.Process | None = None
        self._stdin: asyncio.StreamWriter | None = None
        self._stdout: asyncio.StreamReader | None = None

    async def connect(self) -> None:
        """Launch the server process and establish stdio connection.

        Raises:
            RuntimeError: If process fails to start

        Example:
            >>> transport = StdioTransport(["npx", "server"])
            >>> await transport.connect()
            >>> transport.process is not None
            True
        """
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Failed to create subprocess pipes")

        # Use the process pipes directly as reader/writer
        # No need for custom StreamWriter - just use the stdin directly
        self._stdin = self.process.stdin
        self._stdout = self.process.stdout

    async def send(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server.

        Args:
            message: JSON-RPC message dictionary

        Raises:
            RuntimeError: If not connected

        Example:
            >>> await transport.send({
            ...     "jsonrpc": "2.0",
            ...     "id": 1,
            ...     "method": "ping"
            ... })
        """
        if self._stdin is None:
            raise RuntimeError("Not connected - call connect() first")

        # Serialize message to JSON with newline delimiter
        data = json.dumps(message) + "\n"
        self._stdin.write(data.encode("utf-8"))
        await self._stdin.drain()

    async def receive(self) -> dict[str, Any]:
        """Receive a JSON-RPC message from the server.

        Returns:
            JSON-RPC message dictionary

        Raises:
            RuntimeError: If not connected or connection closed

        Example:
            >>> msg = await transport.receive()
            >>> "jsonrpc" in msg
            True
        """
        if self._stdout is None:
            raise RuntimeError("Not connected - call connect() first")

        # Read until newline
        line = await self._stdout.readline()
        if not line:
            raise RuntimeError("Connection closed by server")

        # Parse JSON
        result: dict[str, Any] = json.loads(line.decode("utf-8"))
        return result

    async def close(self) -> None:
        """Close the connection and terminate the server process.

        Example:
            >>> await transport.close()
            >>> transport.process is None or transport.process.returncode is not None
            True
        """
        if self._stdin:
            self._stdin.close()
            await self._stdin.wait_closed()

        if self.process:
            # Try graceful shutdown first
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                # Force kill if it doesn't terminate
                self.process.kill()
                await self.process.wait()

        self._stdin = None
        self._stdout = None
        self.process = None
