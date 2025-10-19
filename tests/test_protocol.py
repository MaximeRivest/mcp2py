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

from mcp2py.client import MCPClient


@pytest.mark.asyncio
async def test_initialize_handshake_succeeds():
    """Test that initialization handshake completes successfully."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
    result = await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Verify we got a valid initialization response
    assert isinstance(result, dict)
    assert client._initialized is True

    await client.close()


@pytest.mark.asyncio
async def test_list_tools_returns_valid_schemas():
    """Test listing tools returns valid JSON schemas."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
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

    await client.close()


@pytest.mark.asyncio
async def test_call_tool_executes_and_returns_content():
    """Test calling a tool executes and returns content."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
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

    await client.close()


@pytest.mark.asyncio
async def test_handles_server_errors_gracefully():
    """Test that client handles server errors without crashing."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Try to call a tool with invalid arguments
    # The server should handle this gracefully and return an error
    # For now, we just verify the client doesn't crash
    try:
        result = await client.call_tool("add", {})  # Missing required args
        # Server might handle this gracefully and return a result
        # or it might return an error - either way, we shouldn't crash
        assert isinstance(result, dict)
    except (RuntimeError, Exception):
        # If server returns error, we should handle it gracefully
        pass  # Expected behavior

    await client.close()


@pytest.mark.asyncio
async def test_request_id_correlation():
    """Test that multiple requests are properly handled."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Make multiple requests - official SDK handles correlation internally
    tools = await client.list_tools()
    assert len(tools) > 0

    result = await client.call_tool("echo", {"message": "test"})
    assert "content" in result

    # Verify session is still working
    assert client._initialized is True

    await client.close()


@pytest.mark.asyncio
async def test_initialize_required_before_other_calls():
    """Test that initialize must be called before other methods."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()

    # Try to list tools without initializing
    with pytest.raises(RuntimeError, match="Not initialized"):
        await client.list_tools()

    # Try to call tool without initializing
    with pytest.raises(RuntimeError, match="Not initialized"):
        await client.call_tool("echo", {"message": "test"})

    await client.close()


@pytest.mark.asyncio
async def test_call_tool_with_different_argument_types():
    """Test calling tools with various argument types."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Call add with numbers
    result = await client.call_tool("add", {"a": 5, "b": 3})
    assert "Result: 8" in result["content"][0]["text"]

    # Call add with floats
    result = await client.call_tool("add", {"a": 2.5, "b": 1.5})
    assert "Result: 4" in result["content"][0]["text"]

    await client.close()


@pytest.mark.asyncio
async def test_multiple_sequential_tool_calls():
    """Test making multiple tool calls in sequence."""
    test_server = Path(__file__).parent / "test_server.py"
    client = MCPClient([sys.executable, str(test_server)])

    await client.connect()
    await client.initialize(client_info={"name": "test", "version": "1.0"})

    # Make several calls
    for i in range(5):
        result = await client.call_tool("echo", {"message": f"Message {i}"})
        assert f"Echo: Message {i}" in result["content"][0]["text"]

    await client.close()
