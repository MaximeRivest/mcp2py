"""Tests for stdio transport layer."""

import asyncio
import sys
from pathlib import Path

import pytest

from mcp2py.transport import StdioTransport


@pytest.mark.asyncio
async def test_stdio_transport_launches_process():
    """Test that stdio transport successfully launches a subprocess."""
    transport = StdioTransport([sys.executable, "--version"])

    await transport.connect()

    assert transport.process is not None
    assert transport.process.returncode is None  # Still running

    await transport.close()


@pytest.mark.asyncio
async def test_stdio_transport_sends_and_receives_json():
    """Test sending and receiving JSON-RPC messages."""
    # Use our MCP test server
    test_server = Path(__file__).parent.parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    # Send an initialize message (valid MCP protocol)
    await transport.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    })

    # Receive response
    response = await transport.receive()

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    # Should get either result or error, both indicate transport is working
    assert "result" in response or "error" in response

    await transport.close()


@pytest.mark.asyncio
async def test_stdio_transport_multiple_messages():
    """Test sending multiple messages in sequence."""
    test_server = Path(__file__).parent.parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    # Send initialize first
    await transport.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })

    init_response = await transport.receive()
    assert init_response["id"] == 1

    # Send initialized notification
    await transport.send({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    })

    # Now send tools/list request
    await transport.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })

    tools_response = await transport.receive()
    assert tools_response["id"] == 2
    # Just verify we got a response

    await transport.close()


@pytest.mark.asyncio
async def test_stdio_transport_cleanup_on_close():
    """Test that close() properly cleans up resources."""
    test_server = Path(__file__).parent.parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()
    process = transport.process
    assert process is not None

    await transport.close()

    # Process should be terminated
    assert process.returncode is not None
    assert transport._stdin is None
    assert transport._stdout is None
    assert transport.process is None


@pytest.mark.asyncio
async def test_stdio_transport_error_when_not_connected():
    """Test that operations fail gracefully when not connected."""
    transport = StdioTransport([sys.executable, "--version"])

    # Try to send without connecting
    with pytest.raises(RuntimeError, match="Not connected"):
        await transport.send({"jsonrpc": "2.0"})

    # Try to receive without connecting
    with pytest.raises(RuntimeError, match="Not connected"):
        await transport.receive()


@pytest.mark.asyncio
async def test_stdio_transport_invalid_command():
    """Test handling of invalid command."""
    transport = StdioTransport(["nonexistent_command_xyz"])

    # Should raise an error when trying to start invalid command
    with pytest.raises((FileNotFoundError, OSError)):
        await transport.connect()
