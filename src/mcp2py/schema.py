"""Schema and utility functions for MCP integration.

This module provides utilities for:
- Parsing command strings
- Converting between naming conventions (camelCase <-> snake_case)
- JSON Schema to Python type mapping
"""

import re


def parse_command(command: str | list[str]) -> list[str]:
    """Parse command string into list of arguments.

    Args:
        command: Command string or pre-split list

    Returns:
        List of command arguments

    Example:
        >>> parse_command("npx -y weather-server")
        ['npx', '-y', 'weather-server']
        >>> parse_command(["python", "server.py"])
        ['python', 'server.py']
        >>> parse_command("python server.py")
        ['python', 'server.py']
    """
    if isinstance(command, list):
        return command
    return command.split()


def camel_to_snake(name: str) -> str:
    """Convert camelCase or PascalCase to snake_case.

    Args:
        name: Name in camelCase or PascalCase

    Returns:
        Name in snake_case

    Example:
        >>> camel_to_snake("getWeather")
        'get_weather'
        >>> camel_to_snake("fetchData")
        'fetch_data'
        >>> camel_to_snake("HTTPRequest")
        'http_request'
        >>> camel_to_snake("simple")
        'simple'
    """
    # Insert underscore before uppercase letters that follow lowercase
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters that follow lowercase or digit
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase.

    Args:
        name: Name in snake_case

    Returns:
        Name in camelCase

    Example:
        >>> snake_to_camel("get_weather")
        'getWeather'
        >>> snake_to_camel("fetch_data")
        'fetchData'
        >>> snake_to_camel("simple")
        'simple'
    """
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def json_schema_to_python_type(schema: dict[str, object]) -> type:
    """Convert JSON Schema type to Python type.

    Args:
        schema: JSON Schema definition

    Returns:
        Python type object

    Example:
        >>> json_schema_to_python_type({"type": "string"})
        <class 'str'>
        >>> json_schema_to_python_type({"type": "integer"})
        <class 'int'>
        >>> json_schema_to_python_type({"type": "number"})
        <class 'float'>
        >>> json_schema_to_python_type({"type": "boolean"})
        <class 'bool'>
        >>> json_schema_to_python_type({"type": "array"})
        <class 'list'>
        >>> json_schema_to_python_type({"type": "object"})
        <class 'dict'>
    """
    type_map: dict[str, type] = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    json_type_value = schema.get("type", "object")
    # Get the type from string key
    if isinstance(json_type_value, str):
        return type_map.get(json_type_value, object)
    return object
