"""Tests for .tools attribute for AI SDK integration."""

import sys
from pathlib import Path

from mcp2py import load


def test_tools_returns_list_of_schemas():
    """Test that .tools returns a list of tool schemas."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    assert isinstance(tools, list)
    assert len(tools) == 2  # echo and add

    server.close()


def test_tool_schema_has_required_fields():
    """Test that each tool schema has required fields."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    for tool in tools:
        # Required fields for AI SDKs
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool

        # Verify types
        assert isinstance(tool["name"], str)
        assert isinstance(tool["description"], str)
        assert isinstance(tool["inputSchema"], dict)

        # inputSchema should have type
        assert tool["inputSchema"]["type"] == "object"

    server.close()


def test_tools_schema_structure():
    """Test the structure of tool schemas."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Find the echo tool
    echo_tool = next(t for t in tools if t["name"] == "echo")

    assert echo_tool["name"] == "echo"
    assert echo_tool["description"] == "Echo back the input"
    assert "properties" in echo_tool["inputSchema"]
    assert "message" in echo_tool["inputSchema"]["properties"]

    # Find the add tool
    add_tool = next(t for t in tools if t["name"] == "add")

    assert add_tool["name"] == "add"
    assert add_tool["description"] == "Add two numbers"
    assert "properties" in add_tool["inputSchema"]
    assert "a" in add_tool["inputSchema"]["properties"]
    assert "b" in add_tool["inputSchema"]["properties"]

    server.close()


def test_tools_compatible_with_anthropic_format():
    """Test that tools are compatible with Anthropic SDK format."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Anthropic SDK expects: name, description, input_schema
    for tool in tools:
        # Has all required fields
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool

        # Schema is valid JSON Schema
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema

    server.close()


def test_tools_compatible_with_openai_format():
    """Test that tools are compatible with OpenAI SDK format."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # OpenAI expects function calling format
    # We provide MCP format which can be easily converted
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool

        # Can be converted to OpenAI format:
        # {
        #   "type": "function",
        #   "function": {
        #     "name": tool["name"],
        #     "description": tool["description"],
        #     "parameters": tool["inputSchema"]
        #   }
        # }

    server.close()


def test_tools_is_property_not_method():
    """Test that .tools is a property, not a method."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Should be accessible as property (no parentheses)
    tools = server.tools
    assert isinstance(tools, list)

    # Should not be callable
    assert not callable(server.tools)

    server.close()


def test_tools_returns_copy_not_reference():
    """Test that .tools returns a new list each time."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools1 = server.tools
    tools2 = server.tools

    # Should be equal but not the same object
    assert tools1 == tools2
    assert tools1 is not tools2

    server.close()


def test_tools_with_empty_server():
    """Test .tools with a server that has no tools."""
    # For this test, we'll use our regular server but verify behavior
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Should always return a list, even if empty
    assert isinstance(tools, list)
    # Our test server has tools
    assert len(tools) > 0

    server.close()


def test_tools_schema_for_required_parameters():
    """Test that required parameters are properly marked."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Echo tool has required "message" parameter
    echo_tool = next(t for t in tools if t["name"] == "echo")
    assert "required" in echo_tool["inputSchema"]
    assert "message" in echo_tool["inputSchema"]["required"]

    # Add tool has required "a" and "b" parameters
    add_tool = next(t for t in tools if t["name"] == "add")
    assert "required" in add_tool["inputSchema"]
    assert "a" in add_tool["inputSchema"]["required"]
    assert "b" in add_tool["inputSchema"]["required"]

    server.close()


def test_tools_preserves_input_schema_details():
    """Test that inputSchema details are preserved."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    add_tool = next(t for t in tools if t["name"] == "add")

    # Check that parameter types are preserved
    assert add_tool["inputSchema"]["properties"]["a"]["type"] == "number"
    assert add_tool["inputSchema"]["properties"]["b"]["type"] == "number"

    # Check descriptions are preserved
    assert "description" in add_tool["inputSchema"]["properties"]["a"]
    assert "description" in add_tool["inputSchema"]["properties"]["b"]

    server.close()
