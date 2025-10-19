# Release v0.2.0 - Phase 1.4 Complete! 🎉

**Released**: October 19, 2025
**PyPI**: https://pypi.org/project/mcp2py/0.2.0/
**GitHub Tag**: v0.2.0
**Branch**: refactor/use-official-mcp-sdk

---

## 🚀 What's New

This release completes **Phase 1** of the mcp2py implementation, delivering a production-ready, high-level Python API for MCP servers.

### Major Features

#### 1. **`load()` Function** - Simple Entry Point
```python
from mcp2py import load

# Load any MCP server
server = load("python my_server.py")

# Tools become Python methods
result = server.echo(message="Hello!")
result = server.add(a=5, b=3)

# Clean up
server.close()
```

#### 2. **Background Event Loop** - Seamless Async/Sync Bridge
- AsyncRunner class manages event loop in daemon thread
- Synchronous API that "just works"
- No `await` needed in user code
- Thread-safe operation

#### 3. **MCPServer Wrapper** - Dynamic Tool Methods
- Tools exposed as Python methods via `__getattr__`
- Automatic name conversion (camelCase → snake_case)
- Result unwrapping (clean content, not MCP envelope)
- Helpful error messages with available tools

#### 4. **Subprocess Management**
- Launches and maintains server processes
- Clean resource cleanup
- Context manager support
- Proper shutdown on exit

#### 5. **Pythonic Interface**
- Tool name conversion: `getWeather` → `get_weather`
- Both original and snake_case names work
- Clean docstrings from tool descriptions
- Type-safe implementation

---

## 📦 Installation

```bash
pip install mcp2py
```

Or with uv:
```bash
uv add mcp2py
```

---

## 📊 Quality Metrics

✅ **55/55 tests passing** (100% pass rate)
✅ **92% code coverage** (target: >80%)
✅ **mypy --strict clean** (0 type errors)
✅ **33 new tests** added in Phase 1.4
✅ **Full type safety** throughout

### Test Coverage Breakdown
```
Name                       Stmts   Miss  Cover
--------------------------------------------------------
src/mcp2py/__init__.py         5      0   100%
src/mcp2py/client.py          49      2    96%
src/mcp2py/event_loop.py      42      2    95%
src/mcp2py/loader.py          22      2    91%
src/mcp2py/schema.py          18      1    94%
src/mcp2py/server.py          56      8    86%
--------------------------------------------------------
TOTAL                        192     15    92%
```

---

## 🏗️ Architecture

```
User Code (Synchronous)
    ↓
load("python server.py")
    ↓
MCPServer (sync wrapper)
    ↓
AsyncRunner (background event loop in thread)
    ↓
MCPClient (async wrapper around official SDK)
    ↓
mcp.ClientSession (official MCP Python SDK)
    ↓
MCP Server Subprocess (stdio communication)
```

---

## 📝 Implementation Details

### New Files (Phase 1.4)

1. **`src/mcp2py/event_loop.py`** (42 LOC)
   - `AsyncRunner`: Background event loop manager
   - Thread-safe coroutine execution
   - Clean shutdown and resource management

2. **`src/mcp2py/loader.py`** (22 LOC)
   - `load()`: Main entry point
   - Command parsing and subprocess launching
   - Connection and initialization

3. **`src/mcp2py/server.py`** (56 LOC)
   - `MCPServer`: High-level wrapper
   - Dynamic tool method generation
   - Result unwrapping and error handling

4. **`src/mcp2py/schema.py`** (18 LOC)
   - `parse_command()`: String → list parsing
   - `camel_to_snake()`: Name conversion
   - `json_schema_to_python_type()`: Type mapping

### New Tests (Phase 1.4)

1. **`tests/test_event_loop.py`** (11 tests)
   - AsyncRunner execution
   - Exception handling
   - Cleanup and context manager
   - Concurrent operations

2. **`tests/test_schema.py`** (11 tests)
   - Command parsing
   - Name conversion (camel ↔ snake)
   - Type mapping
   - Edge cases

3. **`tests/test_loader.py`** (17 tests)
   - Server loading and initialization
   - Tool calling
   - Error handling
   - Resource cleanup

4. **`tests/test_end_to_end.py`** (5 tests)
   - Complete workflows
   - Realistic usage scenarios
   - Error handling
   - Rapid sequential calls

---

## 🎯 Usage Examples

### Basic Usage
```python
from mcp2py import load

server = load("python tests/test_server.py")
result = server.echo(message="Hello, mcp2py!")
print(result)  # "Echo: Hello, mcp2py!"
server.close()
```

### Context Manager
```python
with load("python server.py") as server:
    result = server.some_tool(arg="value")
# Auto-cleanup
```

### Name Conversion
```python
server = load("npx weather-server")

# Both work:
server.getWeather(city="NYC")      # Original camelCase
server.get_weather(city="NYC")     # Pythonic snake_case
```

### Error Handling
```python
try:
    server.nonexistent_tool()
except AttributeError as e:
    print(e)
    # "Tool 'nonexistent_tool' not found. Available tools: echo, add"
```

---

## 🔄 Migration Guide

This is the first release with the `load()` API, so no migration needed!

If you were using `MCPClient` directly:
```python
# Before (Phase 1.3)
client = MCPClient(["python", "server.py"])
await client.connect()
await client.initialize({"name": "test", "version": "1.0"})
result = await client.call_tool("echo", {"message": "hello"})

# After (Phase 1.4)
server = load("python server.py")
result = server.echo(message="hello")
server.close()
```

---

## 🐛 Known Issues

None! All 55 tests passing.

---

## 📚 What's Next

### Phase 2: Developer Experience (Coming Soon)

1. **Phase 2.1**: `.tools` attribute for AI SDK integration
   ```python
   server = load("npx weather-server")
   react = dspy.ReAct("query -> result", tools=server.tools)
   ```

2. **Phase 2.2**: Resources support
   ```python
   print(server.API_DOCUMENTATION)  # Static resource
   print(server.current_config)     # Dynamic resource
   ```

3. **Phase 2.3**: Prompts support
   ```python
   messages = server.create_weather_report(location="NYC")
   ```

4. **Phase 2.4**: Enhanced error handling
5. **Phase 2.5**: Additional polish

---

## 🙏 Contributors

- **Maxime Rivest** ([@maximerivest](https://github.com/MaximeRivest))
- **Claude Code** (Implementation Assistant)

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/mcp2py/
- **GitHub**: https://github.com/MaximeRivest/mcp2py
- **Issues**: https://github.com/MaximeRivest/mcp2py/issues
- **Documentation**: https://github.com/MaximeRivest/mcp2py#readme

---

**Built with ❤️ using:**
- Official MCP Python SDK
- uv (Python package manager)
- pytest (testing)
- mypy (type checking)
- twine (PyPI publishing)

**Strong and mighty!** 💪
