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
from pathlib import Path
import json

# Use test server from repo
test_server = Path(__file__).parent.parent / "tests" / "test_server.py"

with load(f"python {test_server}") as server:
    # Convert to OpenAI format
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

    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        tools=openai_tools,
        messages=[{"role": "user", "content": "What is 125 plus 75?"}],
    )

    message = response.choices[0].message
    print("GPT response:", response.choices[0].finish_reason)

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        result = getattr(server, tool_call.function.name)(**args)
        print(f"Result: {result}")
