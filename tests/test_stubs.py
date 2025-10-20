"""Tests for stub generation."""

from pathlib import Path
import tempfile

from mcp2py.stubs import generate_stub, get_stub_cache_path, save_stub


def test_generate_stub_with_tools():
    """Test stub generation with tools."""
    tools = [
        {
            "name": "echo",
            "description": "Echo a message",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"}
                },
                "required": ["message"],
            },
        },
        {
            "name": "addNumbers",
            "description": "Add two numbers",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "precision": {"type": "integer", "default": 2},
                },
                "required": ["a", "b"],
            },
        },
    ]

    stub = generate_stub(tools, [], [])

    # Check basic structure
    assert "class MCPServer:" in stub
    assert "from typing import Any" in stub

    # Check tool methods with snake_case conversion
    assert "def echo(self, message: str) -> Any:" in stub
    assert "def add_numbers(self, a: float, b: float, precision: int = 2) -> Any:" in stub

    # Check docstrings
    assert '"""Echo a message"""' in stub
    assert '"""Add two numbers"""' in stub

    # Check lifecycle methods
    assert "def close(self) -> None:" in stub
    assert "def __enter__(self) -> MCPServer:" in stub
    assert "def __exit__(self, *args: Any) -> None:" in stub


def test_generate_stub_with_resources():
    """Test stub generation with resources."""
    resources = [
        {
            "name": "API_DOCS",
            "uri": "resource://docs",
            "description": "API documentation",
        },
        {
            "name": "currentStatus",
            "uri": "resource://status",
            "description": "Current server status",
        },
    ]

    stub = generate_stub([], resources, [])

    # Check resource properties
    assert "@property" in stub
    assert "def api_docs(self) -> Any:" in stub
    assert "def current_status(self) -> Any:" in stub
    assert '"""API documentation"""' in stub
    assert '"""Current server status"""' in stub


def test_generate_stub_with_prompts():
    """Test stub generation with prompts."""
    prompts = [
        {
            "name": "reviewCode",
            "description": "Generate code review prompt",
            "arguments": [
                {"name": "code", "description": "Code to review", "required": True},
                {"name": "focus", "description": "Focus area", "required": False},
            ],
        }
    ]

    stub = generate_stub([], [], prompts)

    # Check prompt methods
    assert "def review_code(self, code: str, focus: str | None = None) -> list[Any]:" in stub
    assert '"""Generate code review prompt"""' in stub


def test_get_stub_cache_path():
    """Test cache path generation."""
    path1 = get_stub_cache_path("python server.py")
    path2 = get_stub_cache_path(["python", "server.py"])

    # Should be in home cache directory
    assert ".cache/mcp2py/stubs" in str(path1)
    assert path1.suffix == ".pyi"

    # Same command in different formats should give same hash
    assert path1 == path2

    # Different commands should give different paths
    path3 = get_stub_cache_path("npx other-server")
    assert path1 != path3


def test_save_stub():
    """Test saving stub to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        stub_path = Path(tmpdir) / "test.pyi"
        content = '"""Test stub."""\n\nclass TestServer:\n    pass\n'

        save_stub(content, stub_path)

        assert stub_path.exists()
        assert stub_path.read_text() == content


def test_generate_complete_stub():
    """Test generating a complete stub with all features."""
    tools = [
        {
            "name": "fetchData",
            "description": "Fetch data from API",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "timeout": {"type": "integer", "default": 30},
                },
                "required": ["url"],
            },
        }
    ]

    resources = [
        {
            "name": "VERSION",
            "uri": "resource://version",
            "description": "Server version",
        }
    ]

    prompts = [
        {
            "name": "explainError",
            "description": "Explain an error message",
            "arguments": [
                {"name": "error", "required": True},
            ],
        }
    ]

    stub = generate_stub(tools, resources, prompts)

    # All sections should be present
    assert "# Tools" in stub
    assert "# Resources" in stub
    assert "# Prompts" in stub
    assert "# Properties" in stub
    assert "# Lifecycle" in stub

    # Check all items present
    assert "def fetch_data" in stub
    assert "def version" in stub
    assert "def explain_error" in stub
    assert "def tools(self) -> list[Any]:" in stub


def test_create_typed_server_class():
    """Test creating a dynamically typed server class."""
    from mcp2py.stubs import create_typed_server_class
    import inspect

    # Mock base class
    class MockServer:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            # Simulate dynamic method lookup
            return lambda **kwargs: f"Called {name}"

    tools = [
        {
            "name": "echo",
            "description": "Echo message",
            "inputSchema": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        }
    ]

    # Create typed class
    TypedClass = create_typed_server_class(MockServer, tools, [], [])

    # Check class was created
    assert TypedClass.__name__ == "MockServerTyped"
    assert issubclass(TypedClass, MockServer)

    # Check method exists with proper signature
    assert hasattr(TypedClass, "echo")
    method = getattr(TypedClass, "echo")
    sig = inspect.signature(method)

    # Check parameters
    params = list(sig.parameters.keys())
    assert "self" in params
    assert "message" in params

    # Check annotations
    assert sig.parameters["message"].annotation == str
