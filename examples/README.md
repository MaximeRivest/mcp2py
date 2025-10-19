# mcp2py AI SDK Examples

Simple examples showing mcp2py with AI frameworks. **Cleanup is automatic.**

## Quick Start

```bash
# Simplest possible - no context manager needed
./examples/simple_example.py

# With AI SDKs
export ANTHROPIC_API_KEY=sk-...  # or OPENAI_API_KEY
./examples/anthropic_example.py
```

**Cleanup is automatic** - use `with load(...)` or just `load()`. Both work!

## Examples

### Anthropic (Claude)

```python
from mcp2py import load
from anthropic import Anthropic

with load("python server.py") as server:
    client = Anthropic()

    response = client.messages.create(
        tools=server.tools,
        messages=[{"role": "user", "content": "What is 125 + 75?"}],
    )

    if response.stop_reason == "tool_use":
        tool_use = next(b for b in response.content if b.type == "tool_use")
        result = getattr(server, tool_use.name)(**tool_use.input)
```

### OpenAI (GPT)

```python
from mcp2py import load
from openai import OpenAI

with load("python server.py") as server:
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

```python
import dspy
from mcp2py import load

with load("python server.py") as server:
    def add_numbers(a: int, b: int) -> int:
        return int(server.add(a=a, b=b).split(": ")[1])

    agent = dspy.ReAct(Calculator, tools=[dspy.Tool(add_numbers)])
    result = agent(question="What is 125 + 75?")
```

## Key Points

- **`with load(...)`** - Context manager handles cleanup automatically
- **Self-contained** - Uses test server from repo, works offline
- **UV scripts** - Dependencies auto-install, just run it
- **Simple** - Shows exactly what you'd write in production

No try/finally, no manual cleanup, no ceremony. **It just works.**
