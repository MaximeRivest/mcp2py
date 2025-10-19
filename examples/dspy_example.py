#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
#     "dspy",
# ]
# ///
"""Using mcp2py with DSPy.

Usage:
    export OPENAI_API_KEY=sk-...
    ./dspy_example.py
"""

import dspy
from mcp2py import load
from pathlib import Path

dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

# Use test server from repo
test_server = Path(__file__).parent.parent / "tests" / "test_server.py"

with load(f"python {test_server}") as server:

    # Wrap MCP tool as callable for DSPy
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers together."""
        result = server.add(a=a, b=b)
        return int(result.split(": ")[1])

    add_tool = dspy.Tool(add_numbers)

    class Calculator(dspy.Signature):
        """Perform calculations."""

        question: str = dspy.InputField()
        answer: str = dspy.OutputField()

    agent = dspy.ReAct(Calculator, tools=[add_tool])
    result = agent(question="What is 125 + 75?")
    print(f"Answer: {result.answer}")
