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

# Load MCP server - use our test server for reliability
import sys
from pathlib import Path

# Use test server from repo for demo
test_server = Path(__file__).parent.parent / "tests" / "test_server.py"
server = load(f"python {test_server}")

try:
    # Create Anthropic client
    client = Anthropic()

    # First call - Claude decides to use add tool
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=server.tools,
        messages=[{"role": "user", "content": "What is 125 plus 75?"}],
    )

    print("Claude's response:", response.stop_reason)

    # If Claude wants to use a tool, execute it
    if response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        print(f"Tool called: {tool_use.name}")
        print(f"Arguments: {tool_use.input}")

        # Execute via mcp2py
        result = getattr(server, tool_use.name)(**tool_use.input)
        print(f"Result: {result}")

finally:
    server.close()
