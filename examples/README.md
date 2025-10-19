# mcp2py Examples

These examples demonstrate how to use mcp2py with popular AI SDKs.

## Features

✨ **Self-contained UV scripts** - No manual dependency installation needed!
🚀 **One-line execution** - Just run them with `uv`
📦 **PEP 723 inline metadata** - Dependencies declared in the script itself

## Quick Start

All examples use UV's inline script metadata (PEP 723). Just run them directly:

```bash
# Set your API key
export ANTHROPIC_API_KEY=your_key_here
# or
export OPENAI_API_KEY=your_key_here

# Run any example
uv run examples/anthropic_example.py
uv run examples/openai_example.py
uv run examples/dspy_example.py

# Or make them executable and run directly
chmod +x examples/*.py
./examples/anthropic_example.py
```

UV will automatically:
- Create a virtual environment
- Install dependencies (mcp2py + the AI SDK)
- Run the script
- Cache everything for next time

## Examples

### 1. Anthropic SDK (Claude)

**File**: `anthropic_example.py`

Shows how to use mcp2py with Claude for function calling:
- Load MCP server
- Pass `server.tools` directly to Anthropic SDK
- Execute tools via mcp2py
- Send results back to Claude

```bash
export ANTHROPIC_API_KEY=your_key_here
uv run examples/anthropic_example.py
```

### 2. OpenAI SDK (GPT-4)

**File**: `openai_example.py`

Shows how to use mcp2py with OpenAI for function calling:
- Load MCP server
- Convert tools to OpenAI format
- Execute tools via mcp2py
- Send results back to GPT-4

```bash
export OPENAI_API_KEY=your_key_here
uv run examples/openai_example.py
```

### 3. DSPy (Agentic Workflows)

**File**: `dspy_example.py`

Shows how to use mcp2py with DSPy ReAct agent:
- Load MCP server
- Create ReAct agent with `server.tools`
- Agent automatically plans and executes tools
- Get final answer

```bash
export OPENAI_API_KEY=your_key_here  # or ANTHROPIC_API_KEY
uv run examples/dspy_example.py
```

## How It Works

Each script has inline metadata at the top:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py",
#     "anthropic",  # or "openai", "dspy"
# ]
# ///
```

This tells UV:
- Python version requirement
- Dependencies to install
- How to run the script

## Development

When running from the mcp2py repository, the scripts automatically use the local version:

```python
# For local development - use local mcp2py if available
if (Path(__file__).parent.parent / "src" / "mcp2py").exists():
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

## Learn More

- [UV Scripts Guide](https://docs.astral.sh/uv/guides/scripts/)
- [PEP 723 - Inline Script Metadata](https://peps.python.org/pep-0723/)
- [mcp2py Documentation](https://github.com/MaximeRivest/mcp2py)
