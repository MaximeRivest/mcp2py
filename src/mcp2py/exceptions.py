"""Custom exceptions for mcp2py.

Provides clear, actionable error messages for common failure modes.
"""


class MCPError(Exception):
    """Base exception for all mcp2py errors.

    All mcp2py exceptions inherit from this base class.
    """
    pass


class MCPConnectionError(MCPError):
    """Failed to connect to MCP server.

    This error occurs when:
    - Server executable not found
    - Server crashes during startup
    - Network connection fails (for remote servers)
    - Server process terminates unexpectedly

    Example:
        >>> from mcp2py import load
        >>> try:
        ...     server = load("nonexistent-command")
        ... except MCPConnectionError as e:
        ...     print(f"Connection failed: {e}")
    """
    pass


class MCPToolError(MCPError):
    """Tool execution failed.

    This error occurs when:
    - Tool call fails on the server
    - Tool returns an error response
    - Tool arguments are invalid

    The error message includes details from the server about what went wrong.

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server")
        >>> try:
        ...     result = server.my_tool(invalid_arg="value")
        ... except MCPToolError as e:
        ...     print(f"Tool failed: {e}")
    """
    pass


class MCPResourceError(MCPError):
    """Resource access failed.

    This error occurs when:
    - Requested resource doesn't exist
    - Resource access is denied
    - Resource fetch fails

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server")
        >>> try:
        ...     data = server.nonexistent_resource
        ... except MCPResourceError as e:
        ...     print(f"Resource not found: {e}")
    """
    pass


class MCPPromptError(MCPError):
    """Prompt execution failed.

    This error occurs when:
    - Requested prompt doesn't exist
    - Prompt arguments are invalid
    - Prompt generation fails

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server")
        >>> try:
        ...     prompt = server.my_prompt(invalid_arg="value")
        ... except MCPPromptError as e:
        ...     print(f"Prompt failed: {e}")
    """
    pass


class MCPValidationError(MCPError):
    """Arguments failed validation.

    This error occurs when:
    - Required arguments are missing
    - Argument types don't match schema
    - Argument values are out of range

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server")
        >>> try:
        ...     server.my_tool()  # Missing required argument
        ... except MCPValidationError as e:
        ...     print(f"Validation failed: {e}")
    """
    pass


class MCPSamplingError(MCPError):
    """Sampling request failed.

    This error occurs when:
    - Sampling is disabled but server requests it
    - LLM API call fails
    - No API keys available for sampling

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server", allow_sampling=False)
        >>> try:
        ...     result = server.tool_that_needs_llm()
        ... except MCPSamplingError as e:
        ...     print(f"Sampling failed: {e}")
    """
    pass


class MCPElicitationError(MCPError):
    """Elicitation request failed.

    This error occurs when:
    - Elicitation is disabled but server requests it
    - User input fails validation
    - Input prompt fails

    Example:
        >>> from mcp2py import load
        >>> server = load("npx my-server", allow_elicitation=False)
        >>> try:
        ...     result = server.tool_that_needs_input()
        ... except MCPElicitationError as e:
        ...     print(f"Elicitation failed: {e}")
    """
    pass


class MCPConfigError(MCPError):
    """Configuration error.

    This error occurs when:
    - Invalid configuration provided
    - Registry file is corrupted
    - Configuration file has syntax errors

    Example:
        >>> from mcp2py import register
        >>> try:
        ...     register(invalid_config=123)  # Invalid type
        ... except MCPConfigError as e:
        ...     print(f"Config error: {e}")
    """
    pass
