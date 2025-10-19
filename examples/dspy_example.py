#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py",
#     "dspy",
# ]
# ///
"""Example: Using mcp2py with DSPy.

This example shows how to use mcp2py's .tools attribute
with DSPy for agentic workflows.

Usage:
    export OPENAI_API_KEY=your_key_here  # or ANTHROPIC_API_KEY
    uv run examples/dspy_example.py

    # Or make it executable:
    chmod +x examples/dspy_example.py
    ./examples/dspy_example.py
"""

import os
import sys
from pathlib import Path

# For local development - use local mcp2py if available
if (Path(__file__).parent.parent / "src" / "mcp2py").exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp2py import load


def main():
    print("🤖 mcp2py + DSPy Example\n")
    print("=" * 60)

    # Check for API key
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("\n⚠️  Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("Example: export OPENAI_API_KEY=your_key_here\n")
        return

    # Load MCP server
    print("\n1. Loading MCP server...")
    test_server = Path(__file__).parent.parent / "tests" / "test_server.py"
    server = load(f"python {test_server}")
    print(f"   ✅ Server loaded with {len(server.tools)} tools")

    # Show tools
    print("\n2. Available tools for DSPy:")
    for tool in server.tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # Use with DSPy
    print("\n3. Setting up DSPy agent...")

    try:
        import dspy

        # Configure DSPy with LLM
        if os.getenv("OPENAI_API_KEY"):
            dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))
            print("   ✅ Using OpenAI GPT-4o-mini")
        else:
            dspy.configure(lm=dspy.LM("anthropic/claude-3-5-sonnet-20241022"))
            print("   ✅ Using Anthropic Claude 3.5 Sonnet")

        # Define signature
        class Calculator(dspy.Signature):
            """Perform calculations using available tools."""

            question: str = dspy.InputField()
            answer: str = dspy.OutputField()

        # Create ReAct agent with tools
        print("\n4. Creating ReAct agent with mcp2py tools...")
        react = dspy.ReAct(Calculator, tools=server.tools)  # ← Pass tools directly!
        print("   ✅ Agent created")

        # Use the agent
        print("\n5. Running agent with calculation task...")
        question = "What is 789 plus 321? Use the add tool."
        print(f"   Question: {question}")

        result = react(question=question)

        print(f"\n   Answer: {result.answer}")

        # The agent automatically:
        # 1. Decides to use the add tool
        # 2. Calls server.add(a=789, b=321)
        # 3. Gets the result
        # 4. Formulates the final answer

        print("\n6. How it works:")
        print("   - DSPy ReAct agent receives mcp2py tools")
        print("   - Agent plans which tools to use")
        print("   - Calls tools via server.<tool_name>(**args)")
        print("   - Combines results into final answer")

    except ImportError:
        print("\n   ⚠️  DSPy not installed")
        print("   Install it with: pip install dspy")
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        import traceback

        traceback.print_exc()

    # Cleanup
    print("\n7. Cleaning up...")
    server.close()
    print("   ✅ Done!")

    print("\n" + "=" * 60)
    print("✨ mcp2py + DSPy = Powerful agentic workflows!")


if __name__ == "__main__":
    main()
