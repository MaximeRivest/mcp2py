#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
#     "anthropic",
# ]
# ///
"""Using mcp2py with Anthropic SDK.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    ./anthropic_example.py
"""

from mcp2py import load
from anthropic import Anthropic

# Load MCP server
server = load("npx -y @modelcontextprotocol/server-everything")

# Create Anthropic client
client = Anthropic()

# Use tools with Claude
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=server.tools,  # ← Pass MCP tools directly!
    messages=[{"role": "user", "content": "Add 125 and 75"}],
)

print(response)
