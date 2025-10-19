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
from pathlib import Path

# Use test server from repo
test_server = Path(__file__).parent.parent / "tests" / "test_server.py"

with load(f"python {test_server}") as server:
    client = Anthropic()

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=server.tools,
        messages=[{"role": "user", "content": "What is 125 plus 75?"}],
    )

    print("Claude's response:", response.stop_reason)

    if response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        result = getattr(server, tool_use.name)(**tool_use.input)
        print(f"Result: {result}")
