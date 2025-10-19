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


def create_function_with_signature(
    name: str,
    description: str,
    input_schema: dict,
    implementation: callable
) -> callable:
    """Create a function with proper signature from JSON schema.

    This creates a real Python function with typed parameters that can be
    inspected by tools like DSPy, inspect.signature(), etc.

    Args:
        name: Function name
        description: Function docstring
        input_schema: JSON Schema for function parameters
        implementation: Callable that takes **kwargs and executes the tool

    Returns:
        Function with proper signature

    Example:
        >>> def impl(**kwargs):
        ...     return f"Called with {kwargs}"
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "url": {"type": "string"},
        ...         "timeout": {"type": "integer", "default": 5000}
        ...     },
        ...     "required": ["url"]
        ... }
        >>> func = create_function_with_signature("test", "Test function", schema, impl)
        >>> import inspect
        >>> sig = inspect.signature(func)
        >>> list(sig.parameters.keys())
        ['url', 'timeout']
    """
    from typing import Any
    import inspect

    # Extract parameters from schema
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))

    # Build parameter list for function signature
    params = []
    for param_name, param_schema in properties.items():
        python_type = json_schema_to_python_type(param_schema)

        # Determine if parameter has a default
        if param_name in required:
            # Required parameter - no default
            param = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=python_type
            )
        else:
            # Optional parameter - use default if provided, otherwise None
            default = param_schema.get("default", None)
            param = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=python_type
            )
        params.append(param)

    # Create signature
    sig = inspect.Signature(
        params,
        return_annotation=Any
    )

    # Create wrapper function that has the right signature
    def wrapper(*args, **kwargs):
        # Bind arguments to our signature
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        # Call implementation with bound arguments
        return implementation(**bound.arguments)

    # Set metadata
    wrapper.__name__ = name
    wrapper.__doc__ = description
    wrapper.__signature__ = sig  # type: ignore
    wrapper.__annotations__ = {
        param.name: param.annotation
        for param in params
    }
    wrapper.__annotations__['return'] = Any

    return wrapper
