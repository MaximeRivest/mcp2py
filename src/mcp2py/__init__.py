"""mcp2py: Turn any MCP server into a Python module.

Example:
    >>> from mcp2py import load
    >>> server = load("npx -y @h1deya/mcp-server-weather")
    >>> result = server.get_alerts(state="CA")
"""

__version__ = "0.1.0"

# Phase 1.3: Protocol layer
from mcp2py.protocol import MCPClient
from mcp2py.transport import StdioTransport

# Will be implemented in later phases
# from mcp2py.loader import load, aload
# from mcp2py.config import configure, register

__all__ = ["MCPClient", "StdioTransport", "__version__"]
