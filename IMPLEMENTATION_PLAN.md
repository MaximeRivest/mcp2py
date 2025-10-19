# mcp2py Implementation Plan

## Overview

Build mcp2py following the README specification with:
- **Robust foundations**: Each phase builds on tested, working code
- **Comprehensive testing**: Behavior-focused tests that survive refactoring
- **Full documentation**: Docstrings with runnable examples
- **uv-based tooling**: Modern Python dependency management

## Technology Stack

- **Package manager**: uv
- **Testing**: pytest + pytest-asyncio
- **Type checking**: mypy (strict mode)
- **Documentation**: Inline docstrings with examples
- **LLM backend**: LiteLLM (supports all providers)
- **MCP transport**: stdio (Phase 1), HTTP/SSE (Phase 2)
- **JSON-RPC**: Custom implementation following MCP spec

## Core Principles

### Testing Philosophy
- **Behavior-driven**: Test what the code does, not how it does it
- **Integration-focused**: Test real MCP servers when possible
- **Mock wisely**: Only mock external APIs (OpenAI, Anthropic), not our code
- **Example-driven**: Every docstring example runs as a test

### Test Categories
1. **Unit tests**: Core utilities (name conversion, schema parsing)
2. **Integration tests**: Real MCP servers (use official test servers)
3. **Doctest**: All docstring examples execute
4. **End-to-end**: Full workflows from README

### Quality Gates (Every Phase)
- ✅ All tests pass (pytest)
- ✅ Type checking passes (mypy --strict)
- ✅ Code coverage > 80%
- ✅ All docstrings complete with examples
- ✅ Examples in docstrings tested via doctest

---

## Phase 1: Core Foundation (Week 1-2)

**Goal**: Basic stdio MCP client that can load servers and call tools

### 1.1 Project Setup & GitHub/PyPI Publishing
**Files**: `pyproject.toml`, `src/mcp2py/__init__.py`, `LICENSE`, `MANIFEST.in`

#### Initial Project Setup
```bash
# Initialize with uv
uv init

# Add dependencies
uv add litellm

# Add dev dependencies
uv add --dev pytest pytest-asyncio mypy pytest-cov build twine

# Create GitHub repo and push
gh repo create mcp2py --public --source=. --remote=origin
git add .
git commit -m "feat: initial project structure"
git push -u origin main
```

#### Project Configuration

**pyproject.toml**:
```toml
[project]
name = "mcp2py"
dynamic = ["version"]
description = "Turn any MCP server into a Python module"
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    { name = "Maxime Rivest", email = "mrive052@gmail.com" }
]
keywords = ["mcp", "model-context-protocol", "ai", "llm", "tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
]

dependencies = [
    "litellm>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "pytest-cov>=4.1.0",
    "build>=1.0.0",
    "twine>=4.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/mcp2py"
Documentation = "https://github.com/yourusername/mcp2py#readme"
Repository = "https://github.com/yourusername/mcp2py"
Issues = "https://github.com/yourusername/mcp2py/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/mcp2py/__init__.py"

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/README.md",
    "/LICENSE",
]

[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=mcp2py --cov-report=term-missing --doctest-modules"
```

#### Version Management

**src/mcp2py/__init__.py**:
```python
"""mcp2py: Turn any MCP server into a Python module.

Example:
    >>> from mcp2py import load
    >>> server = load("npx -y @h1deya/mcp-server-weather")
    >>> result = server.get_alerts(state="CA")
"""

__version__ = "0.1.0"

from mcp2py.loader import load, aload
from mcp2py.config import configure, register

__all__ = ["load", "aload", "configure", "register", "__version__"]
```

#### License

**LICENSE** (MIT):
```text
MIT License

Copyright (c) 2025 Maxime Rivest

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

#### PyPI Publishing Workflow

**scripts/publish.sh**:
```bash
#!/bin/bash
set -e

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Run tests
echo "Running tests..."
uv run pytest

# Type check
echo "Running type check..."
uv run mypy src/mcp2py --strict

# Build
echo "Building package..."
uv run python -m build

# Check build
echo "Checking package..."
uv run twine check dist/*

# Upload to PyPI
echo "Uploading to PyPI..."
uv run twine upload dist/*

echo "✅ Published successfully!"
```

**Makefile** (optional, for convenience):
```makefile
.PHONY: test typecheck build publish clean

test:
	uv run pytest --cov=mcp2py --cov-report=term-missing

typecheck:
	uv run mypy src/mcp2py --strict

build: clean
	uv run python -m build

publish: test typecheck build
	uv run twine upload dist/*

clean:
	rm -rf dist/ build/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

dev-install:
	uv sync --all-extras
```

#### Initial PyPI Release

**Steps for first publish**:
```bash
# 1. Create PyPI account at https://pypi.org/account/register/

# 2. Create API token at https://pypi.org/manage/account/token/

# 3. Configure credentials
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = pypi-AgE...your-token-here...
EOF

# 4. Run publish script
bash scripts/publish.sh

# Or use Makefile
make publish
```

#### GitHub Actions for CI/CD

**.github/workflows/test.yml**:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --all-extras

    - name: Run tests
      run: uv run pytest --cov=mcp2py --cov-report=xml

    - name: Type check
      run: uv run mypy src/mcp2py --strict

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

**.github/workflows/publish.yml**:
```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v1

    - name: Build package
      run: uv run python -m build

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

**Tests**:
- `test_project_structure_valid`
- `test_version_in_init_file`
- `test_version_dynamic_from_init`
- `test_package_builds_successfully`
- `test_license_file_exists`

### 1.2 ✅ COMPLETED - Migrated to Official MCP SDK

**Decision**: Use official `mcp` Python SDK instead of custom implementation

**Rationale**:
- Official SDK is battle-tested and Anthropic-maintained
- Reduces maintenance burden (protocol updates handled by SDK)
- Lighter codebase (deleted 412 LOC of custom code)
- Better foundation for our unique high-level API

**Implementation**: `src/mcp2py/client.py`

**Core class**:
```python
class MCPClient:
    """Wrapper around official MCP SDK's ClientSession.

    Provides same interface as our previous custom implementation,
    but delegates to official SDK for protocol handling.

    Example:
        >>> client = MCPClient(["python", "server.py"])
        >>> await client.connect()
        >>> await client.initialize({"name": "mcp2py", "version": "0.1.0"})
        >>> tools = await client.list_tools()
        >>> result = await client.call_tool("echo", {"message": "hello"})
        >>> await client.close()
    """

    async def connect(self) -> None:
        """Connect via official SDK's stdio_client."""

    async def initialize(self, client_info: dict) -> dict:
        """Initialize using SDK's ClientSession.initialize()."""

    async def list_tools(self) -> list[dict]:
        """List tools using SDK's ClientSession.list_tools()."""

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call tool using SDK's ClientSession.call_tool()."""
```

**Tests**: 11/11 passing
- `test_initialize_handshake_succeeds`
- `test_list_tools_returns_valid_schemas`
- `test_call_tool_executes_and_returns_content`
- `test_handles_server_errors_gracefully`
- `test_request_id_correlation`
- `test_initialize_required_before_other_calls`
- `test_call_tool_with_different_argument_types`
- `test_multiple_sequential_tool_calls`

**Quality metrics**: 88% coverage, mypy --strict clean

### 1.3 Architecture Now

```
mcp2py (our unique value: simple Python API)
    ↓
mcp2py.client.MCPClient (thin wrapper)
    ↓
mcp.ClientSession (official SDK - protocol implementation)
    ↓
MCP Server (any implementation)
```

**Dependencies**:
```toml
dependencies = [
    "mcp>=1.18.0",       # Official MCP Python SDK
    "litellm>=1.0.0",    # For sampling (Phase 3)
]
```

### 1.4 ✅ COMPLETED - High-Level `load()` Function with Background Event Loop

**Decision**: Implemented "The Proper Way™" with background event loop for seamless sync API

**Files**:
- `src/mcp2py/event_loop.py` - AsyncRunner with background event loop
- `src/mcp2py/loader.py` - load() function
- `src/mcp2py/server.py` - MCPServer wrapper
- `src/mcp2py/schema.py` - Utilities (parse_command, camel_to_snake, etc.)

**Implementation**:
```python
def load(command: str, **kwargs) -> MCPServer:
    """Load an MCP server and return a Python module-like interface.

    Args:
        command: Command to run (e.g., "npx weather-server" or URL)
        **kwargs: Additional options

    Returns:
        MCPServer object with tools as methods

    Example:
        >>> server = load("npx -y @h1deya/mcp-server-weather")
        >>> type(server.get_alerts)
        <class 'method'>
        >>> result = server.get_alerts(state="CA")
        >>> isinstance(result, dict)
        True
    """

class MCPServer:
    """Python interface to an MCP server.

    Tools are exposed as methods with proper signatures.
    """

    def __getattr__(self, name: str):
        """Dynamically create tool methods."""
```

**Tests**: 28 new tests across 3 files (all passing)
- `tests/test_event_loop.py` - 11 tests for AsyncRunner
- `tests/test_schema.py` - 11 tests for utilities
- `tests/test_loader.py` - 17 tests for integration

**Key achievements**:
- ✅ Background event loop in daemon thread (AsyncRunner)
- ✅ Synchronous API that "just works"
- ✅ Subprocess management (launches and keeps alive)
- ✅ Tool name conversion (camelCase → snake_case)
- ✅ Result unwrapping (MCP envelope → clean content)
- ✅ Context manager support
- ✅ Clean error messages
- ✅ 92% code coverage
- ✅ mypy --strict clean

**Quality metrics**:
- 50/50 tests passing
- 92% code coverage (target: >80%)
- mypy --strict: 0 errors
- Lines of code: ~192 LOC

### 1.5 Tool Schema to Python Function Mapping
**Status**: Partially implemented in Phase 1.4
**Files**: `src/mcp2py/schema.py`

**Core utilities**:
```python
def json_schema_to_python_type(schema: dict) -> type:
    """Convert JSON schema type to Python type.

    Example:
        >>> json_schema_to_python_type({"type": "string"})
        <class 'str'>
        >>> json_schema_to_python_type({"type": "integer"})
        <class 'int'>
    """

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Example:
        >>> camel_to_snake("getWeather")
        'get_weather'
        >>> camel_to_snake("fetchData")
        'fetch_data'
    """

def create_tool_function(tool_schema: dict, client: MCPClient):
    """Create a Python function from MCP tool schema.

    Example:
        >>> schema = {
        ...     "name": "get_weather",
        ...     "description": "Get weather",
        ...     "inputSchema": {
        ...         "type": "object",
        ...         "properties": {"city": {"type": "string"}},
        ...         "required": ["city"]
        ...     }
        ... }
        >>> func = create_tool_function(schema, client)
        >>> func.__name__
        'get_weather'
        >>> "city" in func.__annotations__
        True
    """
```

**Tests**:
- `test_camel_to_snake_conversion`
- `test_json_schema_to_python_type_mapping`
- `test_create_function_with_correct_signature`
- `test_function_has_docstring_from_description`
- `test_required_params_have_no_defaults`
- `test_optional_params_have_defaults`

**Key behaviors**:
- Names converted to Pythonic snake_case
- Type hints generated from JSON schema
- Required vs optional params handled
- Docstrings generated from descriptions

### Phase 1 Deliverables ✅ COMPLETE
- ✅ `load("python server.py")` works with real MCP servers
- ✅ Tools callable as Python functions (synchronous API)
- ✅ Background event loop for async/sync bridge
- ✅ Subprocess management (launch, keep alive, cleanup)
- ✅ Tool name conversion (camelCase → snake_case)
- ✅ Result unwrapping (clean content, not MCP envelope)
- ✅ Context manager support
- ✅ 50/50 tests passing (28 new tests)
- ✅ 92% code coverage (target: >80%)
- ✅ mypy --strict clean (full type safety)
- ✅ Full docstrings with examples

### Phase 1 Test Strategy
```python
# Integration test with real server
def test_real_weather_server():
    """Test with actual @h1deya/mcp-server-weather."""
    server = load("npx -y @h1deya/mcp-server-weather")

    # Test tool discovery
    assert hasattr(server, 'get_alerts')
    assert hasattr(server, 'get_forecast')

    # Test tool execution
    result = server.get_alerts(state="CA")
    assert isinstance(result, dict)
    assert "content" in result or isinstance(result.get("alerts"), list)

# Docstring examples tested automatically
def test_all_docstring_examples():
    """Run doctest on all modules."""
    import doctest
    import mcp2py

    failures, tests = doctest.testmod(mcp2py, verbose=True)
    assert failures == 0, f"{failures} docstring examples failed"
```

---

## Phase 2: Developer Experience (Week 3-4)

**Goal**: `.tools` attribute, resources, prompts, better errors

### 2.1 Tools Attribute for AI SDKs
**Files**: `src/mcp2py/server.py`

```python
class MCPServer:
    @property
    def tools(self) -> list[dict]:
        """Get tool schemas compatible with all major AI SDKs.

        Returns schemas that work with:
        - Anthropic SDK
        - OpenAI SDK
        - LiteLLM
        - Google Gemini SDK
        - Agno

        Example:
            >>> server = load("npx weather-server")
            >>> tools = server.tools
            >>> len(tools) > 0
            True
            >>> tools[0]["name"]
            'get_alerts'
            >>> "inputSchema" in tools[0]
            True
        """
```

**Tests**:
- `test_tools_returns_list_of_schemas`
- `test_tool_schema_has_required_fields`
- `test_tools_compatible_with_anthropic_sdk`
- `test_tools_compatible_with_openai_sdk`
- `test_tools_compatible_with_litellm`
- `test_tools_compatible_with_gemini_sdk`
- `test_tools_compatible_with_agno`

**Integration examples** (in `examples/` directory):
```python
# examples/anthropic_integration.py
# examples/openai_integration.py
# examples/litellm_integration.py
# examples/gemini_integration.py
# examples/agno_integration.py
```

### 2.2 Resources Implementation
**Files**: `src/mcp2py/resources.py`

```python
def create_resource_accessor(resource_schema: dict, client: MCPClient):
    """Create property or constant for MCP resource.

    Example:
        >>> schema = {"uri": "file:///docs", "name": "docs"}
        >>> accessor = create_resource_accessor(schema, client)
        >>> isinstance(accessor, property) or isinstance(accessor, str)
        True
    """
```

**Tests**:
- `test_list_resources_from_server`
- `test_static_resource_cached`
- `test_dynamic_resource_fetched_on_access`
- `test_resource_names_pythonic`

### 2.3 Prompts Implementation
**Files**: `src/mcp2py/prompts.py`

```python
def create_prompt_function(prompt_schema: dict, client: MCPClient):
    """Create template function from MCP prompt.

    Returns function that returns formatted message list.

    Example:
        >>> schema = {
        ...     "name": "review_code",
        ...     "arguments": [{"name": "code", "required": True}]
        ... }
        >>> func = create_prompt_function(schema, client)
        >>> messages = func(code="def foo(): pass")
        >>> isinstance(messages, list)
        True
    """
```

**Tests**:
- `test_list_prompts_from_server`
- `test_prompt_returns_message_list`
- `test_prompt_arguments_mapped_correctly`

### 2.4 Error Handling & Messages
**Files**: `src/mcp2py/exceptions.py`

```python
class MCPError(Exception):
    """Base exception for mcp2py."""

class MCPConnectionError(MCPError):
    """Cannot connect to MCP server."""

class MCPToolError(MCPError):
    """Tool execution failed."""

class MCPValidationError(MCPError):
    """Invalid arguments provided."""
```

**Tests**:
- `test_connection_error_on_invalid_command`
- `test_tool_error_on_execution_failure`
- `test_validation_error_on_bad_args`
- `test_error_messages_are_helpful`

### 2.5 Context Manager Support
**Files**: `src/mcp2py/server.py`

```python
class MCPServer:
    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Cleanup on exit.

        Example:
            >>> with load("npx server") as server:
            ...     result = server.my_tool()
            >>> # Server process cleaned up automatically
        """
```

**Tests**:
- `test_context_manager_cleans_up_process`
- `test_context_manager_works_with_errors`

### 2.6 AI SDK Compatibility Examples

**Files**: `examples/sdk_integrations/`

Create working examples for all major AI SDKs:

**examples/sdk_integrations/anthropic_example.py**:
```python
"""Example: Using mcp2py with Anthropic SDK."""
import anthropic
from mcp2py import load

def main():
    server = load("npx -y @h1deya/mcp-server-weather")
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=server.tools,  # Works directly!
        messages=[{"role": "user", "content": "What's the weather in Tokyo?"}]
    )

    if response.stop_reason == "tool_use":
        tool_use = response.content[0]
        result = getattr(server, tool_use.name)(**tool_use.input)
        print(result)

if __name__ == "__main__":
    main()
```

**examples/sdk_integrations/openai_example.py**
**examples/sdk_integrations/litellm_example.py**
**examples/sdk_integrations/gemini_example.py**
**examples/sdk_integrations/agno_example.py**

**Tests**:
- `test_anthropic_sdk_integration`
- `test_openai_sdk_integration`
- `test_litellm_integration`
- `test_gemini_sdk_integration`
- `test_agno_integration`

### Phase 2 Deliverables
- ✅ `.tools` attribute works with Anthropic, OpenAI, LiteLLM, Gemini, Agno
- ✅ Working examples for each SDK in `examples/` directory
- ✅ Resources accessible as attributes
- ✅ Prompts return message lists
- ✅ Helpful error messages
- ✅ Context manager cleanup
- ✅ Published to PyPI
- ✅ GitHub repo initialized with CI/CD

---

## Phase 3: Smart Defaults (Week 5-6)

**Goal**: Automatic OAuth, sampling, elicitation

### 3.1 Default Sampling with LiteLLM
**Files**: `src/mcp2py/sampling.py`

```python
class DefaultSamplingHandler:
    """Automatic LLM sampling using LiteLLM.

    Detects API keys from environment and calls appropriate LLM.

    Example:
        >>> import os
        >>> os.environ["OPENAI_API_KEY"] = "sk-test"
        >>> handler = DefaultSamplingHandler()
        >>> handler.can_handle()
        True
    """

    def __call__(self, messages, model_prefs, system_prompt, max_tokens):
        """Call LLM via LiteLLM."""
        import litellm
        response = litellm.completion(
            model=self.model or "gpt-4o-mini",
            messages=messages,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
```

**Tests**:
- `test_sampling_detects_anthropic_key`
- `test_sampling_detects_openai_key`
- `test_sampling_uses_configured_model`
- `test_sampling_disabled_raises_error`
- `test_custom_sampling_handler_used`

**Mock strategy**: Mock `litellm.completion`, not our code

### 3.2 Default Elicitation Handler
**Files**: `src/mcp2py/elicitation.py`

```python
class DefaultElicitationHandler:
    """Terminal-based user input with nice formatting.

    Example:
        >>> handler = DefaultElicitationHandler()
        >>> # In real use, would prompt user
        >>> # For tests, we mock input()
    """

    def __call__(self, message: str, schema: dict):
        """Prompt user for input based on schema."""
```

**Tests**:
- `test_elicitation_prompts_for_string`
- `test_elicitation_prompts_for_boolean`
- `test_elicitation_prompts_for_object`
- `test_elicitation_defaults_used`
- `test_elicitation_disabled_raises_error`

**Mock strategy**: Mock `builtins.input`, validate prompts

### 3.3 Automatic OAuth Flow
**Files**: `src/mcp2py/auth/oauth.py`

```python
class OAuthHandler:
    """Automatic OAuth 2.1 with PKCE.

    Opens browser, handles redirect, stores tokens.

    Example:
        >>> handler = OAuthHandler()
        >>> # In real use, opens browser
        >>> # For tests, we mock the flow
    """

    async def authenticate(self, auth_url: str) -> str:
        """Complete OAuth flow and return token."""
```

**Tests**:
- `test_oauth_detects_401_response`
- `test_oauth_discovers_endpoints`
- `test_oauth_generates_pkce_codes`
- `test_oauth_stores_tokens`
- `test_oauth_refreshes_expired_tokens`
- `test_oauth_disabled_raises_error`

**Mock strategy**: Mock browser open and HTTP callbacks

### 3.4 Integration into `load()`
**Files**: `src/mcp2py/loader.py`

```python
def load(
    command: str,
    *,
    auto_auth: bool = True,
    allow_sampling: bool = True,
    allow_elicitation: bool = True,
    on_sampling: Callable | None = None,
    on_elicitation: Callable | None = None,
    **kwargs
) -> MCPServer:
    """Load MCP server with smart defaults.

    Example:
        >>> # Auto-everything enabled
        >>> server = load("https://api.example.com/mcp")
        >>> # Custom handlers
        >>> server = load("npx server", on_sampling=my_handler)
        >>> # Disabled features
        >>> server = load("npx server", allow_sampling=False)
    """
```

**Tests**:
- `test_load_with_all_defaults_enabled`
- `test_load_with_custom_handlers`
- `test_load_with_features_disabled`

### Phase 3 Deliverables
- ✅ Sampling works automatically with LiteLLM
- ✅ Elicitation prompts in terminal
- ✅ OAuth opens browser and stores tokens
- ✅ All features can be disabled/customized

---

## Phase 4: Advanced Features (Week 7-8)

### 4.1 Async Support (`aload`)
**Files**: `src/mcp2py/async_loader.py`

```python
async def aload(command: str, **kwargs) -> AsyncMCPServer:
    """Async version of load().

    Example:
        >>> server = await aload("npx async-server")
        >>> result = await server.fetch_data(url="...")
    """
```

**Tests**:
- `test_aload_creates_async_server`
- `test_async_tools_awaitable`
- `test_async_context_manager`

### 4.2 HTTP/SSE Transport
**Files**: `src/mcp2py/transport/http.py`

```python
class HTTPTransport:
    """HTTP-based transport with SSE.

    Example:
        >>> transport = HTTPTransport("https://api.example.com/mcp")
        >>> await transport.connect()
    """
```

**Tests**:
- `test_http_transport_connects`
- `test_http_transport_sends_receives`
- `test_http_transport_with_headers`

### 4.3 Server Registry
**Files**: `src/mcp2py/registry.py`

```python
def register(**servers: str) -> None:
    """Register MCP servers.

    Example:
        >>> register(
        ...     weather="npx weather-server",
        ...     api="https://api.example.com/mcp"
        ... )
        >>> server = load("weather")  # Loads from registry
    """
```

**Tests**:
- `test_register_saves_to_config`
- `test_load_uses_registry`
- `test_registry_with_auth`

### 4.4 Roots Support
**Files**: `src/mcp2py/roots.py`

```python
def normalize_roots(roots: str | list[str]) -> list[dict]:
    """Normalize roots to MCP format.

    Example:
        >>> normalize_roots("/tmp")
        [{'uri': 'file:///tmp', 'name': 'tmp'}]
        >>> normalize_roots(["/tmp", "/home"])
        [{'uri': 'file:///tmp', 'name': 'tmp'}, ...]
    """
```

**Tests**:
- `test_roots_string_normalized`
- `test_roots_list_normalized`
- `test_roots_sent_to_server`

### Phase 4 Deliverables
- ✅ Async support fully working
- ✅ HTTP/SSE transport operational
- ✅ Registry system functional
- ✅ Roots support complete

---

## Phase 5: Polish & Documentation (Week 9)

### 5.1 Stub Generation
**Files**: `src/mcp2py/stubs.py`, CLI command

```bash
mcp2py stub "npx weather-server" -o weather.pyi
```

**Tests**:
- `test_stub_generation_creates_valid_pyi`
- `test_stub_has_correct_types`

### 5.2 README Examples as Tests
**Files**: `tests/test_readme_examples.py`

```python
def test_readme_example_basic_usage():
    """Test the basic usage example from README."""
    # Copy-paste from README and verify it works

def test_readme_example_dspy_integration():
    """Test DSPy integration example."""
    # Full example from README

def test_readme_example_async_booking():
    """Test async travel booking example."""
    # Complete async example
```

### 5.3 Performance & Reliability
- Connection pooling for HTTP transport
- Retry logic with exponential backoff
- Request timeouts
- Memory leak prevention

### Phase 5 Deliverables
- ✅ All README examples tested and working
- ✅ Stub generation working
- ✅ Performance optimized
- ✅ Documentation complete

---

## Testing Infrastructure

### Continuous Testing
```bash
# Watch mode during development
uv run pytest --watch

# Full test suite
uv run pytest --cov=mcp2py --cov-report=html

# Type checking
uv run mypy src/mcp2py --strict

# Docstring examples
uv run pytest --doctest-modules src/mcp2py
```

### Test Organization
```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_schema.py
│   ├── test_tools.py
│   └── test_utils.py
├── integration/             # Real MCP servers
│   ├── test_weather_server.py
│   ├── test_filesystem_server.py
│   └── conftest.py          # Shared fixtures
├── e2e/                     # Full workflows
│   ├── test_dspy_integration.py
│   └── test_anthropic_integration.py
├── test_readme_examples.py  # README examples
└── test_doctests.py         # Run all doctests
```

### Fixtures
```python
# tests/conftest.py
import pytest

@pytest.fixture
def weather_server():
    """Real weather MCP server for integration tests."""
    server = load("npx -y @h1deya/mcp-server-weather")
    yield server
    # Cleanup happens via context manager

@pytest.fixture
def mock_llm_response():
    """Mock LiteLLM for testing sampling."""
    with patch('litellm.completion') as mock:
        mock.return_value.choices[0].message.content = "Test response"
        yield mock
```

---

## Success Criteria

### Per Phase
- [ ] All tests pass
- [ ] Type checking clean (mypy --strict)
- [ ] Code coverage > 80%
- [ ] All docstrings complete with examples
- [ ] Docstring examples tested
- [ ] No regressions from previous phases

### Overall Project
- [ ] README examples all work
- [ ] Can load and use 5+ different real MCP servers
- [ ] Works with DSPy, Anthropic SDK, OpenAI SDK
- [ ] Auto-auth, sampling, elicitation all functional
- [ ] Async support complete
- [ ] Full type hint coverage
- [ ] Comprehensive error messages

---

## Development Workflow

### Starting a New Phase
1. Create feature branch: `git checkout -b phase-X-feature-name`
2. Write tests first (TDD when possible)
3. Implement to make tests pass
4. Add docstrings with examples
5. Run full test suite
6. Update README if needed
7. Code review & merge

### Daily Development
```bash
# Setup
uv sync

# Development loop
uv run pytest --watch  # In one terminal
uv run mypy src/mcp2py --watch  # In another

# Before commit
uv run pytest --cov=mcp2py
uv run mypy src/mcp2py --strict
uv run pytest --doctest-modules src/mcp2py

# Commit
git add .
git commit -m "feat: implement X with tests"
```

### Definition of Done
- [ ] Feature works as specified in README
- [ ] Tests written and passing
- [ ] Docstrings complete with examples
- [ ] Type hints complete
- [ ] No mypy errors
- [ ] Code coverage maintained
- [ ] Examples manually tested

---

## Risk Mitigation

### Potential Risks
1. **MCP servers behave inconsistently**: Mitigation: Test with multiple official servers
2. **OAuth flow complex**: Mitigation: Phase it in, mock extensively
3. **LiteLLM API changes**: Mitigation: Pin version, integration tests
4. **Async/sync code duplication**: Mitigation: Share core logic, test both

### Unknowns to Investigate
- [ ] How to best test browser OAuth flow
- [ ] Performance implications of dynamic function generation
- [ ] Best way to handle long-running sampling requests
- [ ] Token refresh edge cases

---

## Timeline Summary

- **Week 1-2**: Phase 1 (Core foundation)
- **Week 3-4**: Phase 2 (Developer experience)
- **Week 5-6**: Phase 3 (Smart defaults)
- **Week 7-8**: Phase 4 (Advanced features)
- **Week 9**: Phase 5 (Polish & docs)

**Total**: ~9 weeks for complete, production-ready library

---

## Next Steps

1. Review this plan
2. Set up project structure with uv
3. Start Phase 1.1 (Project Setup)
4. Begin TDD cycle with first transport tests

Ready to build! 🚀
