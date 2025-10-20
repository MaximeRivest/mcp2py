"""mcp2py: Turn any MCP server into a Python module.

Example:
    >>> from mcp2py import load
    >>> server = load("npx -y @h1deya/mcp-server-weather")
    >>> result = server.get_alerts(state="CA")
"""

__version__ = "0.4.0"

# Phase 1.3: MCP Client (wraps official SDK)
from mcp2py.client import MCPClient

# Phase 1.4: High-level API
from mcp2py.loader import load
from mcp2py.server import MCPServer

# Exceptions
from mcp2py.exceptions import (
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

# Registry and configuration
from mcp2py.registry import register, unregister, list_registered

# Handlers
from mcp2py.sampling import DefaultSamplingHandler
from mcp2py.elicitation import DefaultElicitationHandler

# Will be implemented in later phases
# from mcp2py.loader import aload

__all__ = [
    "load",
    "MCPClient",
    "MCPServer",
    "MCPError",
    "MCPConnectionError",
    "MCPToolError",
    "MCPResourceError",
    "MCPPromptError",
    "MCPValidationError",
    "MCPSamplingError",
    "MCPElicitationError",
    "MCPConfigError",
    "register",
    "unregister",
    "list_registered",
    "DefaultSamplingHandler",
    "DefaultElicitationHandler",
    "__version__",
]
