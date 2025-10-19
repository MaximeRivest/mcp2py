#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py",
#     "anthropic",
# ]
# ///
"""Example: Using mcp2py with Anthropic SDK (Claude).

This example shows how to use mcp2py's .tools attribute
with the Anthropic SDK for function calling.

Usage:
    export ANTHROPIC_API_KEY=your_key_here
    uv run examples/anthropic_example.py

    # Or make it executable:
    chmod +x examples/anthropic_example.py
    ./examples/anthropic_example.py
"""

import os
import sys
from pathlib import Path

# For local development - use local mcp2py if available
if (Path(__file__).parent.parent / "src" / "mcp2py").exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp2py import load


def main():
    print("🤖 mcp2py + Anthropic SDK Example\n")
    print("=" * 60)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  Please set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY=your_key_here\n")
        return

    # Load MCP server
    print("\n1. Loading MCP server...")
    test_server = Path(__file__).parent.parent / "tests" / "test_server.py"
    server = load(f"python {test_server}")
    print(f"   ✅ Server loaded with {len(server.tools)} tools")

    # Show tools
    print("\n2. Available tools:")
    for tool in server.tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # Use with Anthropic SDK
    print("\n3. Using tools with Anthropic SDK...")

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Send message with tools
        print("\n   Sending message to Claude...")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=server.tools,  # ← Pass tools directly!
            messages=[
                {
                    "role": "user",
                    "content": "What is 42 plus 58? Use the add tool to calculate it.",
                }
            ],
        )

        print(f"\n   Response:")
        print(f"   Stop reason: {response.stop_reason}")

        # Handle tool use
        if response.stop_reason == "tool_use":
            tool_use = next(
                block for block in response.content if block.type == "tool_use"
            )

            print(f"\n   Claude wants to use tool: {tool_use.name}")
            print(f"   Arguments: {tool_use.input}")

            # Execute the tool via mcp2py
            print(f"\n   Executing tool via mcp2py...")
            result = getattr(server, tool_use.name)(**tool_use.input)
            print(f"   Result: {result}")

            # Send result back to Claude
            print(f"\n   Sending result back to Claude...")
            final_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=server.tools,
                messages=[
                    {
                        "role": "user",
                        "content": "What is 42 plus 58? Use the add tool to calculate it.",
                    },
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": result,
                            }
                        ],
                    },
                ],
            )

            print(f"\n   Final response:")
            for block in final_response.content:
                if hasattr(block, "text"):
                    print(f"   {block.text}")

    except ImportError:
        print("\n   ⚠️  Anthropic SDK not installed")
        print("   Install it with: pip install anthropic")
    except Exception as e:
        print(f"\n   ❌ Error: {e}")

    # Cleanup
    print("\n4. Cleaning up...")
    server.close()
    print("   ✅ Done!")

    print("\n" + "=" * 60)
    print("✨ This example shows how .tools makes AI SDK integration trivial!")


if __name__ == "__main__":
    main()
