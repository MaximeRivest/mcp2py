# MCP SDK Decision: Official MCP vs FastMCP 2.0

**Date:** 2025-01-19
**Decision:** Which MCP SDK should mcp2py use as a dependency?
**Context:** Our goal is to build a simple, delightful Python API that turns any MCP server into a Python module

---

## Executive Summary

### 🎯 **DECISION: Use Official MCP SDK (`mcp`)**

**Reasons:**
1. ✅ **Minimal dependencies** - Just what we need
2. ✅ **Lower-level API** - More control for our wrapper
3. ✅ **Lighter weight** - Won't bloat user installations
4. ✅ **Official/Canonical** - Anthropic-maintained
5. ✅ **Stable foundation** - FastMCP itself depends on it

---

## Detailed Comparison

### Package Overview

| Aspect | Official MCP SDK (`mcp`) | FastMCP 2.0 (`fastmcp`) |
|--------|-------------------------|------------------------|
| **Version** | 1.18.0 | 2.12.5 |
| **Maintainer** | Anthropic / MCP Team | Jonathan Lowin |
| **Focus** | Protocol implementation | High-level framework |
| **Client API** | `ClientSession` (low-level) | `Client` (high-level) |
| **Server API** | Low-level `Server` | High-level `FastMCP` |
| **Use Case** | Foundation/Building block | Batteries-included framework |

---

## Dependency Analysis

### Official MCP SDK Dependencies

```
mcp==1.18.0 requires:
  ✓ anyio>=4.5              (async primitives)
  ✓ httpx-sse>=0.4          (SSE transport)
  ✓ httpx>=0.27.1           (HTTP client)
  ✓ jsonschema>=4.20.0      (schema validation)
  ✓ pydantic-settings>=2.5.2 (settings management)
  ✓ pydantic<3.0.0,>=2.11.0 (data validation)
  ✓ python-multipart>=0.0.9 (multipart parsing)
  ✓ sse-starlette>=1.6.1    (SSE server)
  ✓ starlette>=0.27         (ASGI framework)
```

**Total: ~10 core dependencies**

**Pros:**
- Focused on MCP protocol essentials
- No extra bloat
- Well-established packages

**Cons:**
- Includes some server-side deps we don't need (starlette, uvicorn)
- But they're lightweight

---

### FastMCP 2.0 Dependencies

```
fastmcp==2.12.5 requires:
  ✓ mcp>=1.12.4,<1.17.0     (official MCP SDK - our target!)
  ✓ authlib>=1.5.2          (OAuth/auth flows)
  ✓ cyclopts>=3.0.0         (CLI parsing)
  ✓ exceptiongroup>=1.2.2   (exception handling)
  ✓ httpx>=0.28.1           (HTTP client)
  ✓ openapi-core>=0.19.5    (OpenAPI validation)
  ✓ openapi-pydantic>=0.5.1 (OpenAPI models)
  ✓ pydantic[email]>=2.11.7 (data validation)
  ✓ pyperclip>=1.9.0        (clipboard operations)
  ✓ python-dotenv>=1.1.0    (env file loading)
  ✓ rich>=13.9.4            (terminal formatting)

Optional:
  ✓ openai>=1.102.0         (OpenAI SDK)
  ✓ websockets>=15.0.1      (WebSocket support)
```

**Total: ~15+ dependencies (includes `mcp` transitively)**

**Pros:**
- Batteries included (auth, OpenAPI, rich formatting)
- High-level Client API
- Advanced features built-in

**Cons:**
- ❌ **Heavy**: Brings in CLI tools, OpenAPI, rich, pyperclip we don't need
- ❌ **Dependency on `mcp`**: We'd get `mcp` transitively anyway
- ❌ **Version pinning**: `mcp<1.17.0` - may lag behind latest MCP
- ❌ **Overlapping features**: We're building our own high-level API

---

## API Comparison

### Official MCP SDK (`mcp`)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Low-level, explicit control
server_params = StdioServerParameters(
    command="npx",
    args=["weather-server"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Full control over protocol
        tools = await session.list_tools()
        resources = await session.list_resources()
        prompts = await session.list_prompts()

        # Raw tool calling
        result = await session.call_tool(
            name="get_forecast",
            arguments={"lat": 37.7, "lon": -122.4}
        )
```

**Characteristics:**
- ✅ Low-level, explicit
- ✅ Full protocol control
- ✅ Perfect for building abstractions
- ✅ Async-native
- ❌ Verbose (we'll hide this)

---

### FastMCP 2.0 (`fastmcp`)

```python
from fastmcp import Client

# High-level, simplified
async with Client("npx weather-server") as client:
    await client.ping()

    # Automatic transport inference
    tools = await client.list_tools()

    # Simplified tool calling
    result = await client.call_tool(
        name="get_forecast",
        arguments={"lat": 37.7, "lon": -122.4}
    )
```

**Characteristics:**
- ✅ High-level, simple
- ✅ Auto transport inference
- ✅ Cleaner syntax
- ❌ Another abstraction layer
- ❌ Less control over protocol details

---

## Alignment with Our Goals

Let's review our README and goals:

### Our Value Proposition

```python
from mcp2py import load

# 🎯 THIS is what we're building:
server = load("npx weather-server")
result = server.get_forecast(latitude=37.7, longitude=-122.4)

# Also:
print(server.tools)  # For AI SDKs
```

### Key Features We're Building

1. **Simple `load()` API** - Hide async complexity
2. **Dynamic Python attributes** - `server.tool_name()`
3. **Type stub generation** - IDE autocomplete
4. **AI SDK integration** - `.tools` property
5. **Smart defaults** - Auth, sampling, elicitation

---

## Why Official MCP SDK Wins

### ✅ 1. We're Building Our Own Abstraction

**FastMCP gives us:**
```python
async with Client("npx server") as client:
    result = await client.call_tool("name", {})
```

**We're building:**
```python
server = load("npx server")  # No async!
result = server.name()        # Python method!
```

**Conclusion:** FastMCP's high-level Client API doesn't help us—we're replacing it entirely with our own abstraction.

---

### ✅ 2. Lighter Dependencies = Better UX

**User installs mcp2py:**

**With `mcp`:**
```bash
pip install mcp2py
# Gets: mcp2py + mcp + litellm + core deps (~20 packages)
```

**With `fastmcp`:**
```bash
pip install mcp2py
# Gets: mcp2py + fastmcp + mcp + authlib + openapi-core +
#       openapi-pydantic + rich + cyclopts + pyperclip +
#       litellm + ... (~35+ packages)
```

**Philosophy:** "It Just Works" includes fast installation and minimal bloat.

---

### ✅ 3. More Control for Our Wrapper

**Official MCP SDK:**
- ✅ Low-level access to protocol details
- ✅ We can implement our own initialization logic
- ✅ We control caching, lazy loading, sync wrappers
- ✅ We can optimize for our use case

**FastMCP:**
- ❌ Another layer between us and the protocol
- ❌ Less flexibility to customize behavior
- ❌ May have opinions that conflict with ours

---

### ✅ 4. Official/Canonical Status

**Official MCP SDK:**
- ✅ Maintained by Anthropic/MCP team
- ✅ Will track protocol spec precisely
- ✅ Long-term support guaranteed
- ✅ First to get new features

**FastMCP:**
- ✅ Well-maintained by community expert
- ⚠️ Depends on official SDK (adds indirection)
- ⚠️ May lag behind spec updates
- ⚠️ Version constraints on `mcp` dependency

---

### ✅ 5. FastMCP Features We Don't Need

FastMCP includes many features for server development:

| Feature | In FastMCP | We Need It? |
|---------|-----------|-------------|
| OAuth flows | ✅ | 🔶 Phase 3 (we'll implement) |
| CLI tools | ✅ | ❌ Not building CLI |
| OpenAPI generation | ✅ | ❌ Not exposing OpenAPI |
| Rich formatting | ✅ | ❌ May use separately if needed |
| Server composition | ✅ | ❌ We're a client only |
| Pyperclip | ✅ | ❌ No clipboard operations |
| Environment vars | ✅ | ✅ Small, we can add python-dotenv |

**Conclusion:** We'd be pulling in 70% features we don't use.

---

## What About FastMCP's Client API?

FastMCP's `Client` is nice, but:

### What FastMCP Client Provides

```python
async with Client("npx server") as client:
    # Automatic transport inference
    await client.ping()
    tools = await client.list_tools()
    result = await client.call_tool(name, args)
```

### What We're Building (Better!)

```python
server = load("npx server")  # Sync!
# Automatic initialization
server.ping()                 # Just works
result = server.tool_name()   # Python method, not call_tool
```

**Our API is SIMPLER than FastMCP's Client.**

So FastMCP's abstraction doesn't help us—we're building an even simpler abstraction on top of the low-level SDK.

---

## Decision Matrix

| Criteria | Official MCP SDK | FastMCP 2.0 | Winner |
|----------|-----------------|-------------|---------|
| **Minimal dependencies** | 10 packages | 15+ packages | 🏆 MCP |
| **Low-level control** | Full control | Wrapped | 🏆 MCP |
| **Official/canonical** | Yes | Community | 🏆 MCP |
| **Client API quality** | Low-level | High-level | 🏆 MCP (we're building our own) |
| **Installation speed** | Fast | Slower | 🏆 MCP |
| **Latest protocol** | Always | Via `mcp` dep | 🏆 MCP |
| **Built-in OAuth** | No | Yes | ⚖️ Neutral (Phase 3) |
| **Built-in CLI** | No | Yes | ⚖️ Neutral (don't need) |
| **OpenAPI support** | No | Yes | ⚖️ Neutral (don't need) |

**Score: Official MCP SDK wins 6-0 (3 neutral)**

---

## Implementation Plan with Official MCP SDK

### Phase 1.4: Refactor to Use MCP SDK

```python
# src/mcp2py/client.py (NEW)
"""Wrapper around official MCP SDK."""

from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """Async wrapper around official MCP ClientSession."""

    def __init__(self, command: str, args: list[str] | None = None):
        self.server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=None
        )
        self._session: ClientSession | None = None
        self._stdio_context = None
        self._session_context = None

    async def connect(self) -> None:
        """Connect to MCP server and initialize."""
        self._stdio_context = stdio_client(self.server_params)
        read, write = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read, write)
        self._session = await self._session_context.__aenter__()

        # Initialize the session
        await self._session.initialize()

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools."""
        result = await self._session.list_tools()
        return result.tools

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any]
    ) -> Any:
        """Call a tool."""
        result = await self._session.call_tool(name, arguments)
        return result

    async def close(self) -> None:
        """Close connection."""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)
```

### Phase 1.5: Build High-Level Wrapper

```python
# src/mcp2py/server.py (NEW)
"""High-level MCPServer wrapper with dynamic methods."""

import asyncio
from typing import Any
from mcp2py.client import MCPClient


class MCPServer:
    """High-level wrapper that makes tools callable as methods."""

    def __init__(self, command: str, args: list[str] | None = None):
        self._client = MCPClient(command, args)
        self._tools: dict[str, dict] = {}
        self._initialized = False
        self._loop = None

    def _ensure_event_loop(self):
        """Get or create event loop."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _sync_run(self, coro):
        """Run async coroutine synchronously."""
        loop = self._ensure_event_loop()
        return loop.run_until_complete(coro)

    def _lazy_init(self):
        """Initialize on first use."""
        if not self._initialized:
            self._sync_run(self._client.connect())
            tools = self._sync_run(self._client.list_tools())

            # Cache tools
            for tool in tools:
                self._tools[self._snake_case(tool.name)] = tool

            self._initialized = True

    def __getattr__(self, name: str) -> callable:
        """Dynamically create tool methods."""
        self._lazy_init()

        if name not in self._tools:
            raise AttributeError(f"Tool '{name}' not found")

        def tool_method(**kwargs):
            return self._sync_run(
                self._client.call_tool(
                    self._tools[name].name,
                    kwargs
                )
            )

        return tool_method

    @property
    def tools(self) -> list[dict[str, Any]]:
        """Get tools in AI SDK format."""
        self._lazy_init()
        return [self._tool_to_schema(t) for t in self._tools.values()]

    @staticmethod
    def _snake_case(name: str) -> str:
        """Convert camelCase to snake_case."""
        # Implementation...

    @staticmethod
    def _tool_to_schema(tool) -> dict[str, Any]:
        """Convert MCP tool to AI SDK format."""
        # Implementation...
```

### Phase 1.6: Simple `load()` Function

```python
# src/mcp2py/loader.py (NEW)
"""Simple load() function."""

from mcp2py.server import MCPServer


def load(command: str, **kwargs) -> MCPServer:
    """Load an MCP server.

    Args:
        command: Command to run (e.g., "npx weather-server")
        **kwargs: Additional options

    Returns:
        MCPServer with tools as methods

    Example:
        >>> server = load("npx -y @h1deya/mcp-server-weather")
        >>> result = server.get_alerts(state="CA")
    """
    # Parse command string
    parts = command.split()
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    return MCPServer(cmd, args, **kwargs)
```

---

## Migration Plan

### What We Delete

```bash
# Remove our custom protocol implementation
rm -rf src/mcp2py/transport/
rm src/mcp2py/protocol.py
rm tests/unit/test_stdio_transport.py
rm tests/test_protocol.py
```

### What We Keep

```bash
# Keep project infrastructure
src/mcp2py/__init__.py
tests/test_server.py  # Our test MCP server
tests/test_project_setup.py
pyproject.toml
README.md
```

### What We Add

```bash
# New implementation on top of official SDK
src/mcp2py/client.py      # Wrapper around ClientSession
src/mcp2py/server.py      # MCPServer with dynamic methods
src/mcp2py/loader.py      # load() function
tests/test_loader.py      # Integration tests
```

### Dependencies

```toml
# pyproject.toml
dependencies = [
    "mcp>=1.18.0",       # Official MCP SDK
    "litellm>=1.0.0",    # For sampling (Phase 3)
]
```

---

## Final Recommendation

### 🎯 Use Official MCP SDK (`mcp`)

**Because:**
1. ✅ **Lighter weight** - Minimal dependencies for users
2. ✅ **More control** - Low-level access to build our abstraction
3. ✅ **Official** - Canonical, Anthropic-maintained
4. ✅ **No redundancy** - FastMCP's Client doesn't help us
5. ✅ **Better UX** - Faster install, less bloat
6. ✅ **Future-proof** - Direct access to latest protocol

**FastMCP is great for:**
- Building MCP servers quickly
- Advanced server patterns (composition, proxying)
- Enterprise auth scenarios
- When you want batteries-included

**But for mcp2py:**
- We're building a **client** (not server)
- We're creating our **own abstraction** (simpler than FastMCP's)
- We want **minimal dependencies**
- We need **low-level control**

**Official MCP SDK is the right choice.**

---

## Next Steps

1. ✅ Add `mcp>=1.18.0` to dependencies
2. ✅ Create new branch: `refactor/use-official-mcp-sdk`
3. ✅ Implement MCPClient wrapper around ClientSession
4. ✅ Build MCPServer with dynamic tool methods
5. ✅ Create `load()` function
6. ✅ Write integration tests
7. ✅ Delete old transport/protocol code
8. ✅ Update documentation

**Timeline:** 2-3 days to complete refactor

---

## Conclusion

**We choose the official `mcp` Python SDK** because it provides exactly what we need—a solid foundation to build our unique, delightful API on top of—without the extra weight of features we don't need.

FastMCP 2.0 is excellent for its use case (rapid server development with batteries included), but for mcp2py's client-focused, minimal-abstraction approach, the official SDK is the perfect fit.

**Let's build on the best foundation available.** 🚀
