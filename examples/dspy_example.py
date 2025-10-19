#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
#     "dspy",
# ]
# ///
"""Using mcp2py with DSPy.

DSPy needs callable functions, so we wrap MCP tools as Python callables.

Usage:
    export OPENAI_API_KEY=sk-...
    ./dspy_example.py
"""

import dspy
from mcp2py import load

# Configure DSPy
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

# Load MCP server
server = load("npx -y @modelcontextprotocol/server-everything")


# Wrap MCP tool as callable for DSPy
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    result = server.add(a=a, b=b)
    return int(result)


# Create DSPy tool
add_tool = dspy.Tool(add_numbers)

# Define agent signature
class Calculator(dspy.Signature):
    """Perform calculations."""

    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


# Create ReAct agent with tools
agent = dspy.ReAct(Calculator, tools=[add_tool])

# Use the agent
result = agent(question="What is 125 + 75?")
print(f"Answer: {result.answer}")
