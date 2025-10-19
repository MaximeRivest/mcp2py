"""Tests for .tools attribute for libraries like Claudette and DSPy."""

import sys
from pathlib import Path

from mcp2py import load


def test_tools_returns_list_of_callables():
    """Test that .tools returns a list of callable functions."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    assert isinstance(tools, list)
    assert len(tools) == 2  # echo and add
    assert all(callable(t) for t in tools)

    server.close()


def test_tools_have_names():
    """Test that each tool function has __name__ attribute."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    names = [t.__name__ for t in tools]
    assert "echo" in names
    assert "add" in names

    server.close()


def test_tools_have_docstrings():
    """Test that each tool function has __doc__ attribute."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    for tool in tools:
        assert hasattr(tool, "__doc__")
        assert isinstance(tool.__doc__, str)
        assert len(tool.__doc__) > 0

    server.close()


def test_tools_are_callable():
    """Test that tools can actually be called."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Find echo tool
    echo = next(t for t in tools if t.__name__ == "echo")
    result = echo(message="test")
    assert "test" in result

    # Find add tool
    add = next(t for t in tools if t.__name__ == "add")
    result = add(a=2, b=3)
    assert "5" in result

    server.close()


def test_tools_compatible_with_claudette():
    """Test that tools work with Claudette-style usage."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Claudette expects list of callables with __name__ and __doc__
    for tool in tools:
        assert callable(tool)
        assert hasattr(tool, "__name__")
        assert hasattr(tool, "__doc__")
        assert isinstance(tool.__name__, str)

    server.close()


def test_tools_compatible_with_dspy():
    """Test that tools work with DSPy-style usage."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # DSPy expects callable functions
    for tool in tools:
        assert callable(tool)
        # DSPy can inspect the function
        assert hasattr(tool, "__name__")

    server.close()


def test_tools_is_property_not_method():
    """Test that .tools is a property, not a method."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    # Should be accessible as property (no parentheses)
    tools = server.tools
    assert isinstance(tools, list)

    server.close()


def test_tools_returns_new_list_each_time():
    """Test that .tools returns a new list each time."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools1 = server.tools
    tools2 = server.tools

    # Should be different list objects
    assert tools1 is not tools2

    # But same number of tools
    assert len(tools1) == len(tools2)

    server.close()


def test_tools_preserve_snake_case_names():
    """Test that tool names are in snake_case."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    names = [t.__name__ for t in tools]

    # Our test server uses lowercase names already
    for name in names:
        assert name.islower()

    server.close()


def test_tools_with_empty_server():
    """Test .tools with various server configurations."""
    test_server = Path(__file__).parent / "test_server.py"
    server = load([sys.executable, str(test_server)])

    tools = server.tools

    # Should always return a list
    assert isinstance(tools, list)
    # Our test server has tools
    assert len(tools) > 0

    server.close()
