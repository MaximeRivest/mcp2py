#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py",
#     "openai",
# ]
# ///
"""Example: Using mcp2py with OpenAI SDK (GPT-4).

This example shows how to use mcp2py's .tools attribute
with the OpenAI SDK for function calling.

Usage:
    export OPENAI_API_KEY=your_key_here
    uv run examples/openai_example.py

    # Or make it executable:
    chmod +x examples/openai_example.py
    ./examples/openai_example.py
"""

import json
import os
import sys
from pathlib import Path

# For local development - use local mcp2py if available
if (Path(__file__).parent.parent / "src" / "mcp2py").exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp2py import load


def mcp_tools_to_openai_format(tools: list[dict]) -> list[dict]:
    """Convert MCP tools to OpenAI function calling format.

    Args:
        tools: MCP tool schemas

    Returns:
        OpenAI-compatible tool definitions
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["inputSchema"],
            },
        }
        for tool in tools
    ]


def main():
    print("🤖 mcp2py + OpenAI SDK Example\n")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY=your_key_here\n")
        return

    # Load MCP server
    print("\n1. Loading MCP server...")
    test_server = Path(__file__).parent.parent / "tests" / "test_server.py"
    server = load(f"python {test_server}")
    print(f"   ✅ Server loaded with {len(server.tools)} tools")

    # Convert to OpenAI format
    print("\n2. Converting tools to OpenAI format...")
    openai_tools = mcp_tools_to_openai_format(server.tools)
    print(f"   ✅ Converted {len(openai_tools)} tools")

    for tool in openai_tools:
        print(f"   - {tool['function']['name']}: {tool['function']['description']}")

    # Use with OpenAI SDK
    print("\n3. Using tools with OpenAI SDK...")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Send message with tools
        print("\n   Sending message to GPT-4...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": "Calculate 123 plus 456 using the available tools.",
                }
            ],
            tools=openai_tools,  # ← Pass converted tools
            tool_choice="auto",
        )

        message = response.choices[0].message
        print(f"\n   Response:")
        print(f"   Finish reason: {response.choices[0].finish_reason}")

        # Handle tool calls
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"\n   GPT-4 wants to use tool: {function_name}")
            print(f"   Arguments: {function_args}")

            # Execute the tool via mcp2py
            print(f"\n   Executing tool via mcp2py...")
            result = getattr(server, function_name)(**function_args)
            print(f"   Result: {result}")

            # Send result back to GPT-4
            print(f"\n   Sending result back to GPT-4...")
            final_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": "Calculate 123 plus 456 using the available tools.",
                    },
                    message,
                    {
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.id,
                    },
                ],
                tools=openai_tools,
            )

            final_message = final_response.choices[0].message
            print(f"\n   Final response:")
            print(f"   {final_message.content}")

    except ImportError:
        print("\n   ⚠️  OpenAI SDK not installed")
        print("   Install it with: pip install openai")
    except Exception as e:
        print(f"\n   ❌ Error: {e}")

    # Cleanup
    print("\n4. Cleaning up...")
    server.close()
    print("   ✅ Done!")

    print("\n" + "=" * 60)
    print("✨ MCP tools work seamlessly with OpenAI function calling!")


if __name__ == "__main__":
    main()
