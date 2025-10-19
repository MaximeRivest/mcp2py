"""Tests for project setup and configuration."""
import mcp2py


def test_version_exists():
    """Test that version is defined."""
    assert hasattr(mcp2py, "__version__")
    assert isinstance(mcp2py.__version__, str)
    assert len(mcp2py.__version__) > 0


def test_version_format():
    """Test that version follows semantic versioning."""
    version = mcp2py.__version__
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
    assert all(part.isdigit() for part in parts[:2]), "Version parts should be numbers"


def test_package_metadata():
    """Test that package has proper metadata."""
    assert mcp2py.__doc__ is not None
    assert "MCP" in mcp2py.__doc__
