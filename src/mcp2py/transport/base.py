"""Base transport protocol for MCP communication."""

from typing import Any, Protocol


class Transport(Protocol):
    """Abstract transport for MCP communication.

    Defines the interface that all MCP transports must implement.
    """

    async def connect(self) -> None:
        """Establish connection to the MCP server.

        Example:
            >>> transport = StdioTransport(["npx", "server"])
            >>> await transport.connect()
        """
        ...

    async def send(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server.

        Args:
            message: JSON-RPC message dictionary

        Example:
            >>> await transport.send({
            ...     "jsonrpc": "2.0",
            ...     "id": 1,
            ...     "method": "initialize",
            ...     "params": {}
            ... })
        """
        ...

    async def receive(self) -> dict[str, Any]:
        """Receive a JSON-RPC message from the server.

        Returns:
            JSON-RPC message dictionary

        Example:
            >>> msg = await transport.receive()
            >>> msg["jsonrpc"]
            '2.0'
        """
        ...

    async def close(self) -> None:
        """Close the connection and cleanup resources.

        Example:
            >>> await transport.close()
        """
        ...
