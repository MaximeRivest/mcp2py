#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
#     "openai",
# ]
# ///
"""Using mcp2py with OpenAI SDK.

Usage:
    export OPENAI_API_KEY=sk-...
    ./openai_example.py
"""

from mcp2py import load
from openai import OpenAI

# Load MCP server
server = load("npx -y @modelcontextprotocol/server-everything")

# Convert MCP tools to OpenAI format
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["inputSchema"],
        },
    }
    for tool in server.tools
]

# Create OpenAI client
client = OpenAI()

# Use tools with GPT
response = client.chat.completions.create(
    model="gpt-4o",
    tools=openai_tools,
    messages=[{"role": "user", "content": "Add 125 and 75"}],
)

print(response)
