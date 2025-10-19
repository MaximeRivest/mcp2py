# mcp2py AI SDK Examples

Simple examples showing how to use mcp2py with popular AI frameworks.

## Quick Start

Each example is a self-contained UV script. Just run it:

```bash
export ANTHROPIC_API_KEY=sk-...  # or OPENAI_API_KEY
./examples/anthropic_example.py
./examples/openai_example.py
./examples/dspy_example.py
```

UV automatically installs dependencies and runs the script.

## Examples

### Anthropic (Claude)

**`anthropic_example.py`** - Pass `server.tools` directly to Claude:

```python
from mcp2py import load
from anthropic import Anthropic

server = load("npx -y @modelcontextprotocol/server-everything")
client = Anthropic()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    tools=server.tools,  # ← Works directly!
    messages=[{"role": "user", "content": "Add 125 and 75"}],
)
```

### OpenAI (GPT-4)

**`openai_example.py`** - Convert tools to OpenAI format:

```python
from mcp2py import load
from openai import OpenAI

server = load("npx -y @modelcontextprotocol/server-everything")

openai_tools = [
    {"type": "function", "function": {
        "name": t["name"],
        "description": t["description"],
        "parameters": t["inputSchema"],
    }}
    for t in server.tools
]

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    tools=openai_tools,
    messages=[{"role": "user", "content": "Add 125 and 75"}],
)
```

### DSPy (Agents)

**`dspy_example.py`** - Wrap MCP tools as callables:

```python
import dspy
from mcp2py import load

dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))
server = load("npx -y @modelcontextprotocol/server-everything")

# Wrap MCP tool as callable
def add_numbers(a: int, b: int) -> int:
    return int(server.add(a=a, b=b))

add_tool = dspy.Tool(add_numbers)

# Create agent
agent = dspy.ReAct(Calculator, tools=[add_tool])
result = agent(question="What is 125 + 75?")
```

## How UV Scripts Work

Each example starts with inline metadata:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
#     "anthropic",
# ]
# ///
```

UV reads this and:
1. Creates a virtual environment
2. Installs dependencies
3. Runs the script
4. Caches everything for next time

No `pip install` needed!
