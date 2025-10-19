"""Tests for MCP server loader and MCPServer wrapper."""

import sys
from pathlib import Path

import pytest

from mcp2py import load
from mcp2py.loader import load as load_func
from mcp2py.server import MCPServer


def test_load_creates_server_object():
    """Test that load() creates an MCPServer instance."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    assert isinstance(server, MCPServer)
    assert hasattr(server, "_client")
    assert hasattr(server, "_runner")
    assert hasattr(server, "_tools")

    server.close()


def test_load_parses_string_command():
    """Test that load() parses string commands correctly."""
    test_server = Path(__file__).parent / "test_server.py"
    cmd = f"{sys.executable} {test_server}"

    server = load(cmd)
    assert isinstance(server, MCPServer)

    server.close()


def test_load_parses_list_command():
    """Test that load() accepts pre-split command list."""
    test_server = Path(__file__).parent / "test_server.py"
    cmd = [sys.executable, str(test_server)]

    server = load(cmd)
    assert isinstance(server, MCPServer)

    server.close()


def test_server_has_callable_tools():
    """Test that server exposes tools as callable attributes."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Check that tools exist and are callable
    assert hasattr(server, "echo")
    assert callable(server.echo)

    assert hasattr(server, "add")
    assert callable(server.add)

    server.close()


def test_tool_call_returns_unwrapped_content():
    """Test that tool calls return unwrapped content."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Call echo tool
    result = server.echo(message="Hello, World!")

    # Should return unwrapped text content
    assert isinstance(result, str)
    assert "Echo: Hello, World!" in result

    server.close()


def test_tool_call_with_different_arguments():
    """Test calling tools with various argument types."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Call add with integers
    result = server.add(a=5, b=3)
    assert "Result: 8" in result

    # Call add with floats
    result = server.add(a=2.5, b=1.5)
    assert "Result: 4" in result

    server.close()


def test_invalid_tool_raises_attributeerror():
    """Test that accessing invalid tool raises AttributeError."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    with pytest.raises(AttributeError) as exc_info:
        server.nonexistent_tool()

    error_msg = str(exc_info.value)
    assert "nonexistent_tool" in error_msg
    assert "not found" in error_msg
    assert "Available tools:" in error_msg

    server.close()


def test_context_manager_cleanup():
    """Test that context manager properly cleans up resources."""
    test_server = Path(__file__).parent / "test_server.py"

    with load([sys.executable, str(test_server)]) as server:
        result = server.echo(message="test")
        assert "Echo: test" in result

    # After context exit, server should be closed
    assert server._closed is True


def test_multiple_tool_calls():
    """Test making multiple sequential tool calls."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Make several calls
    for i in range(5):
        result = server.echo(message=f"Message {i}")
        assert f"Echo: Message {i}" in result

    server.close()


def test_snake_case_tool_names_work():
    """Test that snake_case names work if tools are camelCase."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Our test server has "echo" and "add" (already snake_case)
    # So they should work with their original names
    result = server.echo(message="test")
    assert "Echo: test" in result

    # If we had a camelCase tool like "getWeather", we could call it as:
    # server.get_weather() or server.getWeather()

    server.close()


def test_load_from_exported_function():
    """Test that load is properly exported from main module."""
    test_server = Path(__file__).parent / "test_server.py"
    from mcp2py import load as exported_load

    server = exported_load([sys.executable, str(test_server)])
    assert isinstance(server, MCPServer)

    server.close()


def test_server_close_is_idempotent():
    """Test that calling close() multiple times is safe."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    result = server.echo(message="test")
    assert "test" in result

    server.close()
    server.close()  # Should not raise
    server.close()  # Should not raise


def test_load_empty_command_raises():
    """Test that empty command raises ValueError."""
    with pytest.raises(ValueError, match="Command cannot be empty"):
        load("")


def test_load_invalid_command_raises():
    """Test that invalid command raises RuntimeError."""
    with pytest.raises(RuntimeError, match="Failed to connect"):
        load("nonexistent_command_xyz_123")


def test_tool_method_has_docstring():
    """Test that generated tool methods have docstrings."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    echo_func = server.echo
    assert echo_func.__doc__ == "Echo back the input"

    add_func = server.add
    assert add_func.__doc__ == "Add two numbers"

    server.close()


def test_tool_method_has_name():
    """Test that generated tool methods have correct __name__."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    echo_func = server.echo
    assert echo_func.__name__ == "echo"

    add_func = server.add
    assert add_func.__name__ == "add"

    server.close()


def test_server_handles_concurrent_calls():
    """Test that server can handle rapid sequential calls."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    results = []
    for i in range(10):
        result = server.add(a=i, b=i)
        results.append(result)

    # Verify all calls succeeded
    assert len(results) == 10
    for i, result in enumerate(results):
        expected = i + i
        assert f"Result: {expected}" in result

    server.close()
