"""mcp2py: Turn any MCP server into a Python module.

Example:
    >>> from mcp2py import load
    >>> server = load("npx -y @h1deya/mcp-server-weather")
    >>> result = server.get_alerts(state="CA")
"""

__version__ = "0.1.0"

# Will be implemented in phases
# from mcp2py.loader import load, aload
# from mcp2py.config import configure, register

# __all__ = ["load", "aload", "configure", "register", "__version__"]

__all__ = ["__version__"]
