"""Tests for elicitation handler."""

from unittest.mock import patch

import pytest

from mcp2py import MCPElicitationError
from mcp2py.elicitation import DefaultElicitationHandler


@pytest.fixture
def handler():
    """Create default elicitation handler."""
    return DefaultElicitationHandler()


def test_elicitation_handler_initialization():
    """Test creating elicitation handler."""
    handler = DefaultElicitationHandler()

    assert handler.defaults == {}


def test_elicitation_handler_with_defaults():
    """Test handler with default values."""
    defaults = {"confirm": True, "name": "Test"}
    handler = DefaultElicitationHandler(defaults=defaults)

    assert handler.defaults == defaults


def test_prompt_boolean_yes(handler):
    """Test prompting for boolean with 'y' input."""
    with patch("builtins.input", return_value="y"):
        result = handler._prompt_boolean({"description": "Confirm?"})

        assert result is True


def test_prompt_boolean_no(handler):
    """Test prompting for boolean with 'n' input."""
    with patch("builtins.input", return_value="n"):
        result = handler._prompt_boolean({"description": "Confirm?"})

        assert result is False


def test_prompt_boolean_variants(handler):
    """Test various boolean input variants."""
    for yes_input in ["yes", "YES", "true", "1"]:
        with patch("builtins.input", return_value=yes_input):
            assert handler._prompt_boolean({}) is True

    for no_input in ["no", "NO", "false", "0", "nope"]:
        with patch("builtins.input", return_value=no_input):
            assert handler._prompt_boolean({}) is False


def test_prompt_string(handler):
    """Test prompting for string."""
    with patch("builtins.input", return_value="test value"):
        result = handler._prompt_string({"description": "Enter name"})

        assert result == "test value"


def test_prompt_string_strips_whitespace(handler):
    """Test that string input is stripped."""
    with patch("builtins.input", return_value="  test  "):
        result = handler._prompt_string({})

        assert result == "test"


def test_prompt_integer(handler):
    """Test prompting for integer."""
    with patch("builtins.input", return_value="42"):
        result = handler._prompt_integer({"description": "Enter number"})

        assert result == 42
        assert isinstance(result, int)


def test_prompt_integer_invalid_raises(handler):
    """Test that invalid integer input raises error."""
    with patch("builtins.input", return_value="not a number"):
        with pytest.raises(ValueError):
            handler._prompt_integer({})


def test_prompt_number(handler):
    """Test prompting for float number."""
    with patch("builtins.input", return_value="3.14"):
        result = handler._prompt_number({"description": "Enter number"})

        assert result == 3.14
        assert isinstance(result, float)


def test_prompt_number_accepts_integer(handler):
    """Test that number prompt accepts integer format."""
    with patch("builtins.input", return_value="42"):
        result = handler._prompt_number({})

        assert result == 42.0


def test_prompt_object_all_fields(handler):
    """Test prompting for object with multiple fields."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Your name"},
            "age": {"type": "integer", "description": "Your age"},
            "active": {"type": "boolean", "description": "Active?"}
        },
        "required": ["name"]
    }

    inputs = ["Alice", "30", "y"]
    with patch("builtins.input", side_effect=inputs):
        result = handler._prompt_object(schema)

        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["active"] is True


def test_prompt_object_with_defaults(handler):
    """Test object prompt uses default values."""
    handler = DefaultElicitationHandler(defaults={"name": "Bob"})
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }

    with patch("builtins.input", return_value="25"):
        result = handler._prompt_object(schema)

        assert result["name"] == "Bob"  # From defaults
        assert result["age"] == 25      # From input


def test_prompt_object_optional_fields(handler):
    """Test that optional fields can be skipped."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"}
        },
        "required": ["name"]
    }

    inputs = ["Alice", ""]  # Skip email
    with patch("builtins.input", side_effect=inputs):
        result = handler._prompt_object(schema)

        assert result["name"] == "Alice"
        assert "email" not in result


def test_prompt_object_required_empty_raises(handler):
    """Test that empty required field raises error."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }

    with patch("builtins.input", return_value=""):
        with pytest.raises(ValueError, match="cannot be empty"):
            handler._prompt_object(schema)


def test_call_routes_to_correct_prompt(handler):
    """Test that __call__ routes to correct prompt method."""
    # String
    with patch("builtins.input", return_value="test"):
        result = handler("Enter text", {"type": "string"})
        assert result == "test"

    # Boolean
    with patch("builtins.input", return_value="y"):
        result = handler("Confirm?", {"type": "boolean"})
        assert result is True

    # Integer
    with patch("builtins.input", return_value="42"):
        result = handler("Enter number", {"type": "integer"})
        assert result == 42

    # Number
    with patch("builtins.input", return_value="3.14"):
        result = handler("Enter decimal", {"type": "number"})
        assert result == 3.14


def test_call_keyboard_interrupt_raises_elicitation_error(handler):
    """Test that KeyboardInterrupt is wrapped."""
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with pytest.raises(MCPElicitationError, match="Input failed"):
            handler("Test", {"type": "string"})


def test_call_value_error_wrapped(handler):
    """Test that ValueError is wrapped."""
    with patch("builtins.input", return_value="not_a_number"):
        with pytest.raises(MCPElicitationError, match="Input failed"):
            handler("Enter number", {"type": "integer"})


def test_call_unknown_type_defaults_to_string(handler):
    """Test that unknown schema type defaults to string."""
    with patch("builtins.input", return_value="test"):
        result = handler("Enter value", {"type": "unknown"})
        assert result == "test"


def test_call_no_type_defaults_to_string(handler):
    """Test that missing type defaults to string."""
    with patch("builtins.input", return_value="test"):
        result = handler("Enter value", {})
        assert result == "test"
