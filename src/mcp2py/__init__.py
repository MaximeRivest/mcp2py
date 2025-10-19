"""mcp2py: Turn any MCP server into a Python module.

Example:
    >>> from mcp2py import load
    >>> server = load("npx -y @h1deya/mcp-server-weather")
    >>> result = server.get_alerts(state="CA")
"""

__version__ = "0.1.0"

# Phase 1.3: MCP Client (wraps official SDK)
from mcp2py.client import MCPClient

# Will be implemented in later phases
# from mcp2py.loader import load, aload
# from mcp2py.config import configure, register

__all__ = ["MCPClient", "__version__"]
