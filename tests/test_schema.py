"""Tests for schema utilities."""

from mcp2py.schema import (
    camel_to_snake,
    json_schema_to_python_type,
    parse_command,
    snake_to_camel,
)


def test_parse_command_string():
    """Test parsing command string into list."""
    result = parse_command("npx -y weather-server")
    assert result == ["npx", "-y", "weather-server"]

    result = parse_command("python server.py")
    assert result == ["python", "server.py"]

    result = parse_command("echo hello world")
    assert result == ["echo", "hello", "world"]


def test_parse_command_list():
    """Test parsing command list (pass-through)."""
    cmd = ["python", "server.py"]
    result = parse_command(cmd)
    assert result == cmd
    assert result is cmd  # Should be same object


def test_parse_command_empty_string():
    """Test parsing empty string."""
    result = parse_command("")
    assert result == []  # split() on empty string returns empty list


def test_camel_to_snake_conversion():
    """Test camelCase to snake_case conversion."""
    assert camel_to_snake("getWeather") == "get_weather"
    assert camel_to_snake("fetchData") == "fetch_data"
    assert camel_to_snake("simple") == "simple"
    assert camel_to_snake("HTTPRequest") == "http_request"
    assert camel_to_snake("getUserID") == "get_user_id"
    assert camel_to_snake("IOError") == "io_error"


def test_camel_to_snake_edge_cases():
    """Test edge cases for camel to snake conversion."""
    assert camel_to_snake("") == ""
    assert camel_to_snake("a") == "a"
    assert camel_to_snake("A") == "a"
    assert camel_to_snake("ABC") == "abc"


def test_snake_to_camel_conversion():
    """Test snake_case to camelCase conversion."""
    assert snake_to_camel("get_weather") == "getWeather"
    assert snake_to_camel("fetch_data") == "fetchData"
    assert snake_to_camel("simple") == "simple"
    assert snake_to_camel("http_request") == "httpRequest"


def test_snake_to_camel_edge_cases():
    """Test edge cases for snake to camel conversion."""
    assert snake_to_camel("") == ""
    assert snake_to_camel("a") == "a"
    assert snake_to_camel("_") == ""
    assert snake_to_camel("__") == ""


def test_json_schema_to_python_type_mapping():
    """Test JSON Schema type to Python type mapping."""
    assert json_schema_to_python_type({"type": "string"}) == str
    assert json_schema_to_python_type({"type": "integer"}) == int
    assert json_schema_to_python_type({"type": "number"}) == float
    assert json_schema_to_python_type({"type": "boolean"}) == bool
    assert json_schema_to_python_type({"type": "array"}) == list
    assert json_schema_to_python_type({"type": "object"}) == dict
    assert json_schema_to_python_type({"type": "null"}) == type(None)


def test_json_schema_to_python_type_missing_type():
    """Test type mapping with missing type field."""
    # Should default to object
    assert json_schema_to_python_type({}) == dict


def test_json_schema_to_python_type_unknown_type():
    """Test type mapping with unknown type."""
    # Should default to object
    assert json_schema_to_python_type({"type": "unknown"}) == object


def test_camel_snake_roundtrip():
    """Test roundtrip conversion camel -> snake -> camel."""
    original = "getUserData"
    snake = camel_to_snake(original)
    back = snake_to_camel(snake)
    assert back == original

    original2 = "fetchItems"
    snake2 = camel_to_snake(original2)
    back2 = snake_to_camel(snake2)
    assert back2 == original2
