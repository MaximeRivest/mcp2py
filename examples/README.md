# mcp2py AI SDK Examples

Simple, working examples showing mcp2py with popular AI frameworks.

## Quick Start

```bash
export ANTHROPIC_API_KEY=sk-...  # or OPENAI_API_KEY
./examples/anthropic_example.py
./examples/openai_example.py
./examples/dspy_example.py
```

Each example:
- Uses test server from this repo (reliable, no external dependencies)
- Demonstrates tool calling with AI SDK
- Properly handles server lifecycle
- Self-contained UV script (auto-installs dependencies)

## Examples

### Anthropic (Claude)

Shows Claude function calling with mcp2py:

```python
from mcp2py import load
from anthropic import Anthropic

server = load("python server.py")
client = Anthropic()

response = client.messages.create(
    tools=server.tools,  # ← Pass MCP tools
    messages=[{"role": "user", "content": "What is 125 + 75?"}],
)

# Claude calls tools, we execute via mcp2py
if response.stop_reason == "tool_use":
    tool_use = next(b for b in response.content if b.type == "tool_use")
    result = getattr(server, tool_use.name)(**tool_use.input)
```

### OpenAI (GPT-4)

Shows GPT function calling with format conversion:

```python
from mcp2py import load
from openai import OpenAI

server = load("python server.py")

# Convert to OpenAI format
openai_tools = [
    {"type": "function", "function": {
        "name": t["name"],
        "description": t["description"],
        "parameters": t["inputSchema"],
    }}
    for t in server.tools
]

response = client.chat.completions.create(
    tools=openai_tools,
    messages=[{"role": "user", "content": "What is 125 + 75?"}],
)
```

### DSPy (Agents)

Shows wrapping MCP tools as callables for DSPy:

```python
import dspy
from mcp2py import load

server = load("python server.py")

# DSPy needs callables - wrap MCP tools
def add_numbers(a: int, b: int) -> int:
    result = server.add(a=a, b=b)
    return int(result.split(": ")[1])

add_tool = dspy.Tool(add_numbers)
agent = dspy.ReAct(Calculator, tools=[add_tool])
result = agent(question="What is 125 + 75?")
```

## UV Script Format

Each example uses PEP 723 inline metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["mcp2py>=0.2.0", "anthropic"]
# ///
```

UV automatically installs dependencies and runs the script. No setup needed!
