"""Tests for MCP protocol implementation.

Test naming follows the implementation plan's specification:
- test_initialize_handshake_succeeds
- test_list_tools_returns_valid_schemas
- test_call_tool_executes_and_returns_content
- test_handles_server_errors_gracefully
- test_request_id_correlation
"""

import sys
from pathlib import Path

import pytest

from mcp2py.protocol import MCPClient
from mcp2py.transport import StdioTransport


@pytest.mark.asyncio
async def test_initialize_handshake_succeeds():
    """Test that initialization handshake completes successfully."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    result = await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Verify we got a valid initialization response
    assert isinstance(result, dict)
    assert client._initialized is True

    await transport.close()


@pytest.mark.asyncio
async def test_list_tools_returns_valid_schemas():
    """Test listing tools returns valid JSON schemas."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    tools = await client.list_tools()

    # Verify tools structure
    assert isinstance(tools, list)
    assert len(tools) == 2  # echo and add

    # Verify each tool has required fields
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"
        assert "properties" in tool["inputSchema"]

    # Check specific tools
    tool_names = {tool["name"] for tool in tools}
    assert "echo" in tool_names
    assert "add" in tool_names

    await transport.close()


@pytest.mark.asyncio
async def test_call_tool_executes_and_returns_content():
    """Test calling a tool executes and returns content."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Call echo tool
    result = await client.call_tool("echo", {"message": "Hello, MCP!"})

    # Verify result structure
    assert isinstance(result, dict)
    assert "content" in result
    assert isinstance(result["content"], list)
    assert len(result["content"]) > 0

    # Verify content
    content = result["content"][0]
    assert content["type"] == "text"
    assert "Echo: Hello, MCP!" in content["text"]

    await transport.close()


@pytest.mark.asyncio
async def test_handles_server_errors_gracefully():
    """Test that client handles server errors without crashing."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Try to call a tool with invalid arguments
    # The server should handle this gracefully and return an error
    # For now, we just verify the client doesn't crash
    try:
        result = await client.call_tool("add", {})  # Missing required args
        # Server might handle this gracefully and return a result
        # or it might return an error - either way, we shouldn't crash
        assert isinstance(result, dict)
    except RuntimeError as e:
        # If server returns error, we should handle it gracefully
        assert "tools/call failed" in str(e)

    await transport.close()


@pytest.mark.asyncio
async def test_request_id_correlation():
    """Test that request IDs are properly correlated."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)

    # Make multiple requests and verify IDs increment
    initial_id = client._next_id

    await client.initialize(client_info={"name": "test", "version": "1.0"})
    assert client._next_id == initial_id + 1

    await client.list_tools()
    assert client._next_id == initial_id + 2

    await client.call_tool("echo", {"message": "test"})
    assert client._next_id == initial_id + 3

    await transport.close()


@pytest.mark.asyncio
async def test_initialize_required_before_other_calls():
    """Test that initialize must be called before other methods."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)

    # Try to list tools without initializing
    with pytest.raises(RuntimeError, match="Not initialized"):
        await client.list_tools()

    # Try to call tool without initializing
    with pytest.raises(RuntimeError, match="Not initialized"):
        await client.call_tool("echo", {"message": "test"})

    await transport.close()


@pytest.mark.asyncio
async def test_call_tool_with_different_argument_types():
    """Test calling tools with various argument types."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Call add with numbers
    result = await client.call_tool("add", {"a": 5, "b": 3})
    assert "Result: 8" in result["content"][0]["text"]

    # Call add with floats
    result = await client.call_tool("add", {"a": 2.5, "b": 1.5})
    assert "Result: 4" in result["content"][0]["text"]

    await transport.close()


@pytest.mark.asyncio
async def test_multiple_sequential_tool_calls():
    """Test making multiple tool calls in sequence."""
    test_server = Path(__file__).parent / "test_server.py"
    transport = StdioTransport([sys.executable, str(test_server)])

    await transport.connect()

    client = MCPClient(transport)
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Make several calls
    for i in range(5):
        result = await client.call_tool("echo", {"message": f"Message {i}"})
        assert f"Echo: Message {i}" in result["content"][0]["text"]

    await transport.close()
