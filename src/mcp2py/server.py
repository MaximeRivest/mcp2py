"""MCPServer wrapper providing Pythonic interface to MCP tools, resources, and prompts.

This module provides the MCPServer class which wraps an MCPClient and exposes:
- Tools as Python methods
- Resources as Python attributes (constants or properties)
- Prompts as Python template functions
"""

import atexit
from pathlib import Path
from typing import Any

from mcp2py.client import MCPClient
from mcp2py.event_loop import AsyncRunner
from mcp2py.exceptions import MCPResourceError, MCPPromptError
from mcp2py.schema import camel_to_snake, create_function_with_signature


class MCPServer:
    """Pythonic wrapper around MCP client.

    Exposes MCP tools as Python methods, resources as attributes,
    and prompts as template functions.

    Example:
        >>> # Typically created via load(), not directly
        >>> from mcp2py import load
        >>> server = load("python tests/test_server.py")
        >>> result = server.echo(message="Hello!")
        >>> "Hello!" in result
        True
        >>> server.close()
    """

    def __init__(
        self,
        client: MCPClient,
        runner: AsyncRunner,
        tools: list[dict[str, Any]],
        resources: list[dict[str, Any]],
        prompts: list[dict[str, Any]],
        command: str | list[str] | None = None,
    ) -> None:
        """Initialize MCP server wrapper.

        Args:
            client: Connected MCPClient instance
            runner: AsyncRunner for sync/async bridge
            tools: List of tool schemas from server
            resources: List of resource schemas from server
            prompts: List of prompt schemas from server
            command: Command used to start server (for stub caching)
        """
        self._client = client
        self._runner = runner
        self._tools = {tool["name"]: tool for tool in tools}
        self._resources = {res["name"]: res for res in resources}
        self._prompts = {prompt["name"]: prompt for prompt in prompts}
        self._command = command
        self._closed = False

        # Create bidirectional mapping: snake_case <-> original
        self._name_map: dict[str, str] = {}
        self._resource_name_map: dict[str, str] = {}
        self._prompt_name_map: dict[str, str] = {}

        for original_name in self._tools.keys():
            snake_name = camel_to_snake(original_name)
            if snake_name != original_name:
                self._name_map[snake_name] = original_name

        for original_name in self._resources.keys():
            snake_name = camel_to_snake(original_name)
            if snake_name != original_name:
                self._resource_name_map[snake_name] = original_name

        for original_name in self._prompts.keys():
            snake_name = camel_to_snake(original_name)
            if snake_name != original_name:
                self._prompt_name_map[snake_name] = original_name

        # Register cleanup on exit (for REPL/notebook usage without 'with')
        atexit.register(self.close)

    def __getattr__(self, name: str) -> Any:
        """Dynamically create tool methods, resource properties, or prompt functions.

        Args:
            name: Tool/resource/prompt name (snake_case or original)

        Returns:
            Callable for tool/prompt, or value for resource

        Raises:
            AttributeError: If not found
            MCPResourceError: If resource fetch fails
            MCPPromptError: If prompt execution fails

        Example:
            >>> server = load("python tests/test_server.py")
            >>> echo_func = server.echo
            >>> callable(echo_func)
            True
            >>> server.close()
        """
        # Try tools first (most common)
        tool_name = self._name_map.get(name) or (name if name in self._tools else None)
        if tool_name:
            tool_schema = self._tools[tool_name]

            def tool_method(**kwargs: Any) -> Any:
                result = self._runner.run(self._client.call_tool(tool_name, kwargs))
                return self._unwrap_result(result)

            tool_method.__name__ = name
            tool_method.__doc__ = tool_schema.get("description", "")
            return tool_method

        # Try resources second
        resource_name = self._resource_name_map.get(name) or (
            name if name in self._resources else None
        )
        if resource_name:
            resource_schema = self._resources[resource_name]
            uri = resource_schema["uri"]
            try:
                result = self._runner.run(self._client.read_resource(uri))
                contents = result.get("contents", [])
                if contents and len(contents) == 1:
                    # Single content item - return text or blob
                    item = contents[0]
                    return item.get("text") or item.get("blob")
                return contents
            except Exception as e:
                raise MCPResourceError(
                    f"Failed to fetch resource '{name}': {e}"
                ) from e

        # Try prompts third
        prompt_name = self._prompt_name_map.get(name) or (
            name if name in self._prompts else None
        )
        if prompt_name:
            prompt_schema = self._prompts[prompt_name]
            description = prompt_schema.get("description", "")
            arguments = prompt_schema.get("arguments", [])

            # Build input schema from arguments
            properties = {}
            required = []
            for arg in arguments:
                arg_name = arg["name"]
                properties[arg_name] = {
                    "type": "string",  # Prompts typically use strings
                    "description": arg.get("description", ""),
                }
                if arg.get("required", False):
                    required.append(arg_name)

            input_schema = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

            # Create implementation
            def make_prompt_impl(_prompt_name: str = prompt_name):
                def impl(**kwargs: Any) -> Any:
                    try:
                        result = self._runner.run(
                            self._client.get_prompt(_prompt_name, kwargs)
                        )
                        return result.get("messages", [])
                    except Exception as e:
                        raise MCPPromptError(
                            f"Failed to execute prompt '{name}': {e}"
                        ) from e

                return impl

            # Create function with proper signature
            prompt_func = create_function_with_signature(
                name=name,
                description=description,
                input_schema=input_schema,
                implementation=make_prompt_impl(),
            )

            return prompt_func

        # Not found in any category
        available_tools = sorted(set(list(self._name_map.keys()) + list(self._tools.keys())))
        available_resources = sorted(
            set(list(self._resource_name_map.keys()) + list(self._resources.keys()))
        )
        available_prompts = sorted(
            set(list(self._prompt_name_map.keys()) + list(self._prompts.keys()))
        )

        raise AttributeError(
            f"'{name}' not found.\n"
            f"Available tools: {', '.join(available_tools) if available_tools else 'none'}\n"
            f"Available resources: {', '.join(available_resources) if available_resources else 'none'}\n"
            f"Available prompts: {', '.join(available_prompts) if available_prompts else 'none'}"
        )

    @property
    def tools(self) -> list[Any]:
        """Get list of callable tool functions.

        Returns callable functions for libraries like Claudette and DSPy
        that expect Python functions rather than JSON schemas.

        Each function has:
        - __name__: Tool name (snake_case)
        - __doc__: Tool description
        - Proper function signature with typed parameters
        - Callable interface

        Returns:
            List of callable tool functions

        Example:
            >>> server = load("python tests/test_server.py")
            >>> tools = server.tools
            >>> len(tools) > 0
            True
            >>> callable(tools[0])
            True
            >>> tools[0].__name__
            'echo'
            >>> server.close()
        """
        from mcp2py.schema import create_function_with_signature

        tool_functions = []
        for tool_name in self._tools.keys():
            # Get snake_case version if available
            snake_name = None
            for snake, orig in self._name_map.items():
                if orig == tool_name:
                    snake_name = snake
                    break

            # Use snake_case name if available, otherwise original
            name = snake_name if snake_name else tool_name

            # Get tool schema
            tool_schema = self._tools[tool_name]
            input_schema = tool_schema.get("inputSchema", {})
            description = tool_schema.get("description", "")

            # Create implementation that captures tool_name in closure
            def make_implementation(_tool_name: str = tool_name):
                def impl(**kwargs: Any) -> Any:
                    result = self._runner.run(self._client.call_tool(_tool_name, kwargs))
                    return self._unwrap_result(result)
                return impl

            # Create function with proper signature from JSON schema
            tool_func = create_function_with_signature(
                name=name,
                description=description,
                input_schema=input_schema,
                implementation=make_implementation()
            )

            tool_functions.append(tool_func)

        return tool_functions

    def _unwrap_result(self, result: dict[str, Any]) -> Any:
        """Extract content from MCP response.

        Args:
            result: Raw MCP tool call result

        Returns:
            Unwrapped content (string if single text, list otherwise)

        Example:
            >>> server = load("python tests/test_server.py")
            >>> # Results are automatically unwrapped
            >>> result = server.echo(message="test")
            >>> isinstance(result, str)
            True
            >>> server.close()
        """
        content = result.get("content", [])

        # If single text response, return just the text
        if len(content) == 1 and content[0].get("type") == "text":
            return content[0]["text"]

        # Otherwise return full content list
        return content

    def close(self) -> None:
        """Close connection and cleanup resources.

        Terminates the server subprocess and stops the background event loop.

        Example:
            >>> server = load("python tests/test_server.py")
            >>> server.close()
        """
        if self._closed:
            return

        self._closed = True

        # Unregister atexit handler (if called explicitly)
        try:
            atexit.unregister(self.close)
        except Exception:
            pass

        # Close client connection (stops subprocess)
        try:
            self._runner.run(self._client.close())
        except Exception:
            pass

        # Stop event loop
        try:
            self._runner.close()
        except Exception:
            pass

    def __enter__(self) -> "MCPServer":
        """Enter context manager.

        Example:
            >>> with load("python tests/test_server.py") as server:
            ...     result = server.echo(message="test")
            ...     "test" in result
            True
        """
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager and cleanup.

        Example:
            >>> with load("python tests/test_server.py") as server:
            ...     pass
            ... # Automatically closed
        """
        self.close()

    def __del__(self) -> None:
        """Safety net cleanup on garbage collection."""
        try:
            self.close()
        except Exception:
            pass

    def generate_stubs(self, path: str | Path | None = None) -> Path:
        """Generate .pyi stub file for IDE autocomplete support.

        Args:
            path: Optional path to save stub file. If None, saves to cache.

        Returns:
            Path where stub file was saved

        Example:
            >>> server = load("python tests/test_server.py")
            >>> stub_path = server.generate_stubs("./stubs/server.pyi")
            >>> stub_path.exists()
            True
            >>> server.close()
        """
        from mcp2py.stubs import generate_stub, get_stub_cache_path, save_stub

        # Generate stub content
        tools_list = list(self._tools.values())
        resources_list = list(self._resources.values())
        prompts_list = list(self._prompts.values())

        stub_content = generate_stub(tools_list, resources_list, prompts_list)

        # Determine save path
        if path is None:
            if self._command is None:
                raise ValueError("Cannot auto-cache stub: no command provided")
            save_path = get_stub_cache_path(self._command)
        else:
            save_path = Path(path)

        # Save stub file
        save_stub(stub_content, save_path)

        return save_path
