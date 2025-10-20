"""Stub file generation for IDE autocomplete support.

This module generates .pyi stub files from MCP server schemas,
providing type hints and autocomplete for IDEs. It also creates
dynamic typed classes that IDEs can understand without configuration.
"""

import hashlib
import inspect
from pathlib import Path
from typing import Any, TYPE_CHECKING

from mcp2py.schema import camel_to_snake, json_schema_to_python_type


def create_typed_server_class(
    base_class: type,
    tools: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
) -> type:
    """Create a dynamically typed server class with proper type hints.

    This creates a subclass of MCPServer that has method stubs with
    proper type annotations, allowing IDEs to provide autocomplete
    without any configuration.

    Args:
        base_class: The MCPServer class to extend
        tools: List of tool schemas
        resources: List of resource schemas
        prompts: List of prompt schemas

    Returns:
        A new class that extends base_class with typed methods
    """
    from typing import get_type_hints

    # Build class dictionary with typed method stubs
    class_dict = {}
    annotations = {}

    # Add tool method stubs
    for tool in tools:
        tool_name = tool["name"]
        snake_name = camel_to_snake(tool_name)
        input_schema = tool.get("inputSchema", {})
        description = tool.get("description", "")

        # Create method stub with signature
        method_func = _create_tool_method_stub(snake_name, description, input_schema)
        class_dict[snake_name] = method_func

    # Add resource property stubs
    for resource in resources:
        resource_name = resource["name"]
        snake_name = camel_to_snake(resource_name)
        description = resource.get("description", "")

        # Create property that delegates to __getattr__
        def make_resource_property(name: str, desc: str):
            """Create a property that delegates to __getattr__."""
            @property
            def resource_property(self) -> Any:
                # Delegate to __getattr__ for the actual implementation
                return object.__getattribute__(self, '__getattr__')(name)
            resource_property.__doc__ = desc
            return resource_property

        class_dict[snake_name] = make_resource_property(snake_name, description)

    # Add prompt method stubs
    for prompt in prompts:
        prompt_name = prompt["name"]
        snake_name = camel_to_snake(prompt_name)
        description = prompt.get("description", "")
        arguments = prompt.get("arguments", [])

        # Create prompt method stub
        method_func = _create_prompt_method_stub(snake_name, description, arguments)
        class_dict[snake_name] = method_func

    # Create the new class
    typed_class = type(
        f"{base_class.__name__}Typed",
        (base_class,),
        class_dict
    )

    return typed_class


def _create_tool_method_stub(name: str, description: str, input_schema: dict) -> Any:
    """Create a typed method stub for a tool."""
    # Extract parameters from schema
    properties = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))

    # Build parameter list
    params = [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]

    for param_name, param_schema in properties.items():
        python_type = json_schema_to_python_type(param_schema)

        if param_name in required:
            param = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=python_type
            )
        else:
            default = param_schema.get("default", None)
            param = inspect.Parameter(
                param_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=python_type
            )
        params.append(param)

    # Create signature
    sig = inspect.Signature(params, return_annotation=Any)

    # Create stub function that delegates to __getattr__
    def stub_method(self, *args, **kwargs):
        # Bind args to signature to get proper kwargs
        bound = sig.bind(self, *args, **kwargs)
        bound.apply_defaults()
        # Remove 'self' from arguments
        call_kwargs = {k: v for k, v in bound.arguments.items() if k != 'self'}
        # Call the real implementation via __getattr__
        real_method = object.__getattribute__(self, '__getattr__')(name)
        return real_method(**call_kwargs)

    stub_method.__name__ = name
    stub_method.__doc__ = description
    stub_method.__signature__ = sig  # type: ignore

    return stub_method


def _create_resource_property_stub(description: str) -> Any:
    """Create a typed property stub for a resource."""
    def stub_getter(self) -> Any:
        # Delegate to __getattr__ for the real implementation
        # The property name will be determined by the class_dict key
        # But we can't access it here, so this won't work as a property
        # Resources should use the same method approach
        raise NotImplementedError("Resources accessed as properties - use __getattr__")

    stub_getter.__doc__ = description
    return stub_getter


def _create_prompt_method_stub(name: str, description: str, arguments: list) -> Any:
    """Create a typed method stub for a prompt."""
    # Build parameter list
    params = [inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD)]

    for arg in arguments:
        arg_name = arg["name"]
        if arg.get("required", False):
            param = inspect.Parameter(
                arg_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=str
            )
        else:
            param = inspect.Parameter(
                arg_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation=str | None
            )
        params.append(param)

    # Create signature
    sig = inspect.Signature(params, return_annotation=list[Any])

    # Create stub function that delegates to __getattr__
    def stub_method(self, *args, **kwargs):
        # Bind args to signature to get proper kwargs
        bound = sig.bind(self, *args, **kwargs)
        bound.apply_defaults()
        # Remove 'self' from arguments
        call_kwargs = {k: v for k, v in bound.arguments.items() if k != 'self'}
        # Call the real implementation via __getattr__
        real_method = object.__getattribute__(self, '__getattr__')(name)
        return real_method(**call_kwargs)

    stub_method.__name__ = name
    stub_method.__doc__ = description
    stub_method.__signature__ = sig  # type: ignore

    return stub_method


def generate_stub(
    tools: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    prompts: list[dict[str, Any]],
    class_name: str = "MCPServer",
) -> str:
    """Generate .pyi stub file content from MCP schemas.

    Args:
        tools: List of tool schemas
        resources: List of resource schemas
        prompts: List of prompt schemas
        class_name: Name of the class to generate (default: MCPServer)

    Returns:
        String content of .pyi stub file

    Example:
        >>> tools = [{
        ...     "name": "echo",
        ...     "description": "Echo a message",
        ...     "inputSchema": {
        ...         "type": "object",
        ...         "properties": {"message": {"type": "string"}},
        ...         "required": ["message"]
        ...     }
        ... }]
        >>> stub = generate_stub(tools, [], [])
        >>> "def echo" in stub
        True
    """
    lines = [
        '"""Auto-generated stub file for MCP server."""',
        "",
        "from typing import Any",
        "",
        "",
        f"class {class_name}:",
        '    """MCP Server interface with tools, resources, and prompts."""',
        "",
    ]

    # Generate tool methods
    if tools:
        lines.append("    # Tools")
        for tool in tools:
            tool_name = tool["name"]
            snake_name = camel_to_snake(tool_name)
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})

            # Build method signature
            params = []
            properties = input_schema.get("properties", {})
            required = set(input_schema.get("required", []))

            for param_name, param_schema in properties.items():
                python_type = json_schema_to_python_type(param_schema)
                type_name = _type_to_string(python_type)

                if param_name in required:
                    params.append(f"{param_name}: {type_name}")
                else:
                    default = param_schema.get("default")
                    if default is None:
                        params.append(f"{param_name}: {type_name} | None = None")
                    elif isinstance(default, str):
                        params.append(f'{param_name}: {type_name} = "{default}"')
                    else:
                        params.append(f"{param_name}: {type_name} = {default}")

            params_str = ", ".join(params)

            # Add docstring if present
            if description:
                lines.append(f"    def {snake_name}(self, {params_str}) -> Any:")
                lines.append(f'        """{description}"""')
                lines.append("        ...")
            else:
                lines.append(f"    def {snake_name}(self, {params_str}) -> Any: ...")

            lines.append("")

    # Generate resource properties
    if resources:
        lines.append("    # Resources")
        for resource in resources:
            resource_name = resource["name"]
            snake_name = camel_to_snake(resource_name)
            description = resource.get("description", "")

            if description:
                lines.append("    @property")
                lines.append(f"    def {snake_name}(self) -> Any:")
                lines.append(f'        """{description}"""')
                lines.append("        ...")
            else:
                lines.append("    @property")
                lines.append(f"    def {snake_name}(self) -> Any: ...")

            lines.append("")

    # Generate prompt methods
    if prompts:
        lines.append("    # Prompts")
        for prompt in prompts:
            prompt_name = prompt["name"]
            snake_name = camel_to_snake(prompt_name)
            description = prompt.get("description", "")
            arguments = prompt.get("arguments", [])

            # Build method signature from prompt arguments
            params = []
            for arg in arguments:
                arg_name = arg["name"]
                if arg.get("required", False):
                    params.append(f"{arg_name}: str")
                else:
                    params.append(f"{arg_name}: str | None = None")

            params_str = ", ".join(params)

            if description:
                lines.append(f"    def {snake_name}(self, {params_str}) -> list[Any]:")
                lines.append(f'        """{description}"""')
                lines.append("        ...")
            else:
                lines.append(f"    def {snake_name}(self, {params_str}) -> list[Any]: ...")

            lines.append("")

    # Add tools property
    lines.append("    # Properties")
    lines.append("    @property")
    lines.append("    def tools(self) -> list[Any]:")
    lines.append('        """Get list of callable tool functions."""')
    lines.append("        ...")
    lines.append("")

    # Add lifecycle methods
    lines.append("    # Lifecycle")
    lines.append("    def close(self) -> None:")
    lines.append('        """Close connection and cleanup resources."""')
    lines.append("        ...")
    lines.append("")

    lines.append(f"    def __enter__(self) -> {class_name}:")
    lines.append('        """Enter context manager."""')
    lines.append("        ...")
    lines.append("")

    lines.append("    def __exit__(self, *args: Any) -> None:")
    lines.append('        """Exit context manager and cleanup."""')
    lines.append("        ...")

    return "\n".join(lines)


def _type_to_string(python_type: type) -> str:
    """Convert Python type to string representation for stub.

    Args:
        python_type: Python type object

    Returns:
        String representation for stub file

    Example:
        >>> _type_to_string(str)
        'str'
        >>> _type_to_string(int)
        'int'
        >>> _type_to_string(list)
        'list'
    """
    type_map = {
        str: "str",
        int: "int",
        float: "float",
        bool: "bool",
        list: "list",
        dict: "dict",
        type(None): "None",
    }
    return type_map.get(python_type, "Any")


def get_stub_cache_path(command: str | list[str]) -> Path:
    """Get cache path for stub file based on command.

    Args:
        command: Command string or list used to start server

    Returns:
        Path to cached stub file

    Example:
        >>> path = get_stub_cache_path("python server.py")
        >>> path.name.endswith('.pyi')
        True
    """
    # Normalize command to string
    if isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    # Create hash of command for unique filename
    command_hash = hashlib.sha256(command_str.encode()).hexdigest()[:16]

    # Cache directory
    cache_dir = Path.home() / ".cache" / "mcp2py" / "stubs"
    cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir / f"{command_hash}.pyi"


def save_stub(
    stub_content: str,
    path: Path | str,
) -> None:
    """Save stub content to file.

    Args:
        stub_content: Generated stub file content
        path: Path to save stub file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stub_content)
