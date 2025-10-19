# Release v0.3.0 - Proper Function Signatures for AI Frameworks

**Release Date:** October 19, 2025
**GitHub Tag:** [v0.3.0](https://github.com/MaximeRivest/mcp2py/releases/tag/v0.3.0)
**PyPI:** [mcp2py 0.3.0](https://pypi.org/project/mcp2py/0.3.0/)

## 🎯 Major Feature: Dynamic Function Signature Generation

This release fixes a critical compatibility issue with DSPy, Claudette, and other AI frameworks that inspect function signatures to determine tool parameters.

### The Problem

Previously, mcp2py provided tools as generic `**kwargs` functions:

```python
def new_page(_tool_name: str = 'new_page', **kwargs: Any) -> Any:
    """Creates a new page"""
```

AI frameworks like DSPy couldn't determine what parameters to pass, leading to errors like:

```
anyio.ClosedResourceError
MCP error -32602: Invalid arguments for tool new_page: Required parameter 'url' missing
```

### The Solution

Now mcp2py dynamically generates functions with **proper signatures** from MCP JSON schemas:

```python
def new_page(url: str, timeout: int = None) -> Any:
    """Creates a new page

    Args:
        url: URL to load in a new page
        timeout: Maximum wait time in milliseconds
    """
```

## ✨ What's New

### 1. **Dynamic Function Signature Generation**

New `create_function_with_signature()` function in `schema.py`:
- Parses JSON Schema to extract parameter information
- Creates real Python `inspect.Parameter` objects
- Handles required vs optional parameters correctly
- Applies default values from schema
- Generates proper type annotations

### 2. **Updated `.tools` Property**

The `.tools` property now returns functions with:
- ✅ Proper parameter names and types
- ✅ Required vs optional parameter distinction
- ✅ Default values from JSON schema
- ✅ Type annotations for IDE support
- ✅ Full `inspect.signature()` compatibility

### 3. **Full Framework Compatibility**

Works seamlessly with:
- **DSPy**: `dspy.ReAct(Signature, tools=server.tools)`
- **Claudette**: `Chat(model="claude-3-5-sonnet", tools=server.tools)`
- **LangChain**: Tool schemas with proper parameters
- **Custom frameworks**: Any tool that inspects function signatures

### 4. **Better Developer Experience**

```python
import inspect
from mcp2py import load

browser = load("npx chrome-devtools-mcp@latest")

# IDE autocomplete works!
browser.new_page(url="https://example.com", timeout=5000)

# Inspect signatures
tool = [t for t in browser.tools if t.__name__ == 'new_page'][0]
print(inspect.signature(tool))
# Output: (url: str, timeout: int = None) -> Any

# Clear validation errors
try:
    browser.new_page()  # Missing required parameter
except TypeError as e:
    print(e)  # missing a required argument: 'url'
```

## 🔧 Technical Details

### New Functions

**`schema.py: create_function_with_signature()`**
- Dynamically creates Python functions from JSON Schema
- Uses `inspect.Parameter` for proper signature construction
- Handles type mapping: `string` → `str`, `integer` → `int`, etc.
- Preserves parameter order from schema
- Applies defaults correctly

### Updated Components

**`server.py: MCPServer.tools` property**
- Generates functions with proper signatures (not `**kwargs`)
- Creates closure to capture tool name correctly
- Applies signature using `__signature__` attribute
- Sets `__annotations__` for type checkers

## 📦 Installation

```bash
pip install mcp2py==0.3.0
```

Or with uv:

```bash
uv add mcp2py
```

## 🧪 Testing

All 65 tests passing with 87% code coverage:

```bash
uv run pytest
# 65 passed in 111.67s
```

New test coverage:
- Signature generation correctness
- Parameter type mapping
- Required vs optional handling
- Default value application
- DSPy/Claudette compatibility

## 📚 Examples

### DSPy Integration (Fixed!)

```python
from mcp2py import load
import dspy

dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

browser = load("npx chrome-devtools-mcp@latest")

# DSPy now understands tool parameters!
agent = dspy.ReAct("task -> result", tools=browser.tools)
result = agent(task="Open https://example.com and take a screenshot")
```

### Signature Inspection

```python
from mcp2py import load
import inspect

server = load("python my_server.py")

for tool in server.tools:
    sig = inspect.signature(tool)
    print(f"{tool.__name__}{sig}")
    # Outputs: tool_name(param1: str, param2: int = 5) -> Any
```

## 🔄 Migration Guide

### From v0.2.x to v0.3.0

**No breaking changes!** This release is fully backward compatible.

Your existing code continues to work:

```python
from mcp2py import load

server = load("npx my-server")
result = server.my_tool(arg1="value", arg2=42)  # Still works!
```

**What's new:**

The `.tools` property now returns better functions:

```python
# Before (v0.2.x): Generic signature
tool.__signature__  # Not present or generic **kwargs

# After (v0.3.0): Proper signature
tool.__signature__  # Signature(url: str, timeout: int = None)
```

## 🐛 Bug Fixes

- Fixed DSPy compatibility (tools now have inspectable signatures)
- Fixed Claudette integration (proper callable functions)
- Fixed IDE autocomplete for tool parameters
- Fixed parameter validation error messages

## 🙏 Acknowledgments

Thanks to users who reported DSPy integration issues that led to this improvement!

## 📊 Stats

- **Lines of Code:** 283 (+28 from v0.2.0)
- **Test Coverage:** 87%
- **Tests Passing:** 65/65
- **Type Checking:** mypy --strict ✅

## 🔗 Links

- **PyPI:** https://pypi.org/project/mcp2py/0.3.0/
- **GitHub:** https://github.com/MaximeRivest/mcp2py
- **Documentation:** README.md
- **Examples:** `examples/` directory

## 📅 What's Next

Coming in future releases:

- **Phase 2:** Resources and Prompts support
- **Phase 3:** Automatic sampling, elicitation, OAuth
- **Phase 4:** Async support (`aload()`), HTTP/SSE transport
- **Phase 5:** Type stub generation, server registry

---

**Install now:** `pip install mcp2py==0.3.0`

**Full Changelog:** https://github.com/MaximeRivest/mcp2py/compare/v0.2.0...v0.3.0
