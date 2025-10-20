"""Tests for custom exceptions."""

import pytest

from mcp2py import (
    MCPError,
    MCPConnectionError,
    MCPToolError,
    MCPResourceError,
    MCPPromptError,
    MCPValidationError,
    MCPSamplingError,
    MCPElicitationError,
    MCPConfigError,
)


def test_all_exceptions_inherit_from_base():
    """All mcp2py exceptions should inherit from MCPError."""
    exceptions = [
        MCPConnectionError,
        MCPToolError,
        MCPResourceError,
        MCPPromptError,
        MCPValidationError,
        MCPSamplingError,
        MCPElicitationError,
        MCPConfigError,
    ]

    for exc_class in exceptions:
        assert issubclass(exc_class, MCPError)


def test_exceptions_are_raisable():
    """Test that all exceptions can be raised and caught."""
    with pytest.raises(MCPError):
        raise MCPError("Base error")

    with pytest.raises(MCPConnectionError):
        raise MCPConnectionError("Connection failed")

    with pytest.raises(MCPToolError):
        raise MCPToolError("Tool failed")

    with pytest.raises(MCPResourceError):
        raise MCPResourceError("Resource not found")

    with pytest.raises(MCPPromptError):
        raise MCPPromptError("Prompt failed")

    with pytest.raises(MCPValidationError):
        raise MCPValidationError("Validation failed")

    with pytest.raises(MCPSamplingError):
        raise MCPSamplingError("Sampling failed")

    with pytest.raises(MCPElicitationError):
        raise MCPElicitationError("Elicitation failed")

    with pytest.raises(MCPConfigError):
        raise MCPConfigError("Config error")


def test_exceptions_preserve_messages():
    """Test that exception messages are preserved."""
    message = "Test error message"

    try:
        raise MCPToolError(message)
    except MCPToolError as e:
        assert str(e) == message


def test_specific_exception_caught_by_base():
    """Test that specific exceptions can be caught as MCPError."""
    with pytest.raises(MCPError):
        raise MCPToolError("Tool failed")

    with pytest.raises(MCPError):
        raise MCPConnectionError("Connection failed")


def test_exception_chaining():
    """Test that exceptions support chaining."""
    original = ValueError("Original error")

    try:
        raise MCPToolError("Tool failed") from original
    except MCPToolError as e:
        assert e.__cause__ is original
        assert isinstance(e.__cause__, ValueError)
