#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp>=0.5.0",
# ]
# ///
"""Full-featured MCP test server using FastMCP.

Demonstrates all MCP capabilities:
- Tools: Basic functions and sampling/elicitation
- Resources: Documentation and server information
- Prompts: Code review and README generation templates
"""

from fastmcp import FastMCP
from fastmcp.server import Context
from pydantic import BaseModel

# Create FastMCP server
mcp = FastMCP("test-server")


# ============================================================================
# MODELS
# ============================================================================

class ConfirmResponse(BaseModel):
    confirm: bool


# ============================================================================
# TOOLS
# ============================================================================

@mcp.tool()
def echo(message: str) -> str:
    """Echo back the input message.

    Args:
        message: Message to echo back
    """
    return f"Echo: {message}"


@mcp.tool()
def add(a: float, b: float) -> str:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number
    """
    result = a + b
    return f"Result: {result}"


@mcp.tool()
async def analyze_sentiment(text: str, ctx: Context) -> str:
    """Analyze sentiment of text using LLM (triggers sampling).

    Args:
        text: Text to analyze for sentiment
    """
    # Request LLM completion from client
    from mcp.types import SamplingMessage, TextContent

    result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"Analyze the sentiment of this text and respond with just one word (positive, negative, or neutral): {text}"
                )
            )
        ],
        max_tokens=10
    )

    # Extract response
    if hasattr(result.content, 'text'):
        sentiment = result.content.text
    else:
        sentiment = str(result.content)

    return f"Sentiment: {sentiment.strip()}"


@mcp.tool()
async def confirm_action(action: str, ctx: Context) -> str:
    """Ask user to confirm an action (triggers elicitation).

    Args:
        action: Action to confirm with the user
    """
    result = await ctx.elicit(
        message=f"Do you want to {action}?",
        response_type=ConfirmResponse
    )

    # FastMCP wraps the response in AcceptedElicitation with .data attribute
    if result and hasattr(result, 'data') and result.data and result.data.confirm:
        return f"Action '{action}' confirmed and executed!"
    else:
        return f"Action '{action}' cancelled."


# ============================================================================
# RESOURCES
# ============================================================================

@mcp.resource("resource://documentation")
def get_documentation() -> str:
    """Complete API documentation for mcp2py."""
    return """# mcp2py API Documentation

## Overview
mcp2py turns MCP servers into Python modules with a simple, synchronous API.

## Core Functions

### load(command, **kwargs)
Load an MCP server and return a Python interface.

**Parameters:**
- `command` (str | list[str]): Command to launch server
- `roots` (optional): Directory roots for the server
- `allow_sampling` (bool): Allow LLM sampling (default: True)
- `allow_elicitation` (bool): Allow user input prompts (default: True)

**Returns:** MCPServer object with tools as methods

**Example:**
```python
from mcp2py import load

server = load("npx -y @modelcontextprotocol/server-filesystem /tmp")
result = server.list_directory(path="/tmp")
```

### register(**servers)
Register servers with friendly names.

**Example:**
```python
from mcp2py import register

register(
    weather="npx -y @h1deya/mcp-server-weather",
    fs="npx -y @modelcontextprotocol/server-filesystem /tmp"
)
```

## Classes

### MCPServer
Pythonic wrapper around MCP client.

**Properties:**
- `tools`: List of callable tool functions with proper signatures

**Methods:**
- Tool methods are generated dynamically from server capabilities

## Exceptions

- `MCPError`: Base exception for all mcp2py errors
- `MCPConnectionError`: Failed to connect to server
- `MCPToolError`: Tool execution failed
- `MCPResourceError`: Resource access failed
- `MCPPromptError`: Prompt execution failed
"""


@mcp.resource("resource://version")
def get_version() -> str:
    """Current version and build information."""
    import json
    import sys

    return json.dumps({
        "version": "0.4.0",
        "build": "20250119",
        "python_version": sys.version,
        "protocol_version": "2024-11-05"
    }, indent=2)


@mcp.resource("resource://stats")
def get_stats() -> str:
    """Real-time server statistics."""
    import json
    import time

    return json.dumps({
        "uptime_seconds": 0,
        "tools_called": 0,
        "last_call": None,
        "timestamp": time.time()
    }, indent=2)


# ============================================================================
# PROMPTS
# ============================================================================

@mcp.prompt()
def review_code(code: str, focus: str = "general quality") -> str:
    """Generate a code review prompt for Python code.

    Args:
        code: Python code to review
        focus: Specific aspect to focus on (style, bugs, performance)
    """
    return f"""Please review the following Python code with a focus on {focus}:

```python
{code}
```

Provide feedback on:
1. Code correctness and potential bugs
2. Code style and readability
3. Performance considerations
4. Best practices and patterns
5. Suggestions for improvement

Be specific and constructive in your feedback."""


@mcp.prompt()
def generate_readme(project_name: str, description: str, features: str = "") -> str:
    """Generate a README.md template for a project.

    Args:
        project_name: Name of the project
        description: Short description of the project
        features: Comma-separated list of key features
    """
    features_list = ""
    if features:
        features_list = "\n".join(f"- {f.strip()}" for f in features.split(","))

    return f"""Generate a comprehensive README.md file for a project with these details:

**Project Name:** {project_name}
**Description:** {description}
**Key Features:**
{features_list}

The README should include:
1. Project title and description
2. Installation instructions
3. Quick start guide with code examples
4. Feature list
5. Usage examples
6. Contributing guidelines
7. License information

Make it professional, clear, and engaging."""


@mcp.prompt()
def explain_mcp() -> str:
    """Explain what MCP (Model Context Protocol) is."""
    return """Explain what the Model Context Protocol (MCP) is and why it's useful.

Cover:
1. What problem does MCP solve?
2. How does MCP work at a high level?
3. What are the key concepts (tools, resources, prompts)?
4. What are some practical use cases?
5. How does mcp2py make MCP easier to use from Python?

Provide a clear, concise explanation suitable for a developer new to MCP."""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
