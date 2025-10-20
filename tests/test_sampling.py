"""Tests for sampling handler."""

import os
from unittest.mock import Mock, patch

import pytest

from mcp2py import MCPSamplingError
from mcp2py.sampling import DefaultSamplingHandler


@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock litellm module."""
    mock = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock.completion.return_value = mock_response

    # Make sure sampling imports our mock
    import sys
    sys.modules["litellm"] = mock

    yield mock

    # Cleanup
    if "litellm" in sys.modules:
        del sys.modules["litellm"]


def test_sampling_handler_initialization():
    """Test creating sampling handler."""
    handler = DefaultSamplingHandler()

    assert handler.model is None


def test_sampling_handler_with_explicit_model():
    """Test handler with explicit model."""
    handler = DefaultSamplingHandler(model="gpt-4")

    assert handler.model == "gpt-4"


def test_can_handle_with_explicit_model():
    """Test can_handle returns True with explicit model."""
    handler = DefaultSamplingHandler(model="gpt-4")

    assert handler.can_handle() is True


def test_can_handle_with_openai_key(monkeypatch):
    """Test can_handle detects OpenAI API key."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    handler = DefaultSamplingHandler()

    assert handler.can_handle() is True


def test_can_handle_with_anthropic_key(monkeypatch):
    """Test can_handle detects Anthropic API key."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    handler = DefaultSamplingHandler()

    assert handler.can_handle() is True


def test_can_handle_with_google_key(monkeypatch):
    """Test can_handle detects Google API key."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    handler = DefaultSamplingHandler()

    assert handler.can_handle() is True


def test_can_handle_without_keys(monkeypatch):
    """Test can_handle returns False without keys."""
    # Clear all API key env vars
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    handler = DefaultSamplingHandler()

    assert handler.can_handle() is False


def test_call_with_explicit_model(mock_litellm):
    """Test calling handler with explicit model."""
    handler = DefaultSamplingHandler(model="gpt-4")

    result = handler(
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100
    )

    assert result == "Test response"
    mock_litellm.completion.assert_called_once()
    call_args = mock_litellm.completion.call_args
    assert call_args[1]["model"] == "gpt-4"


def test_call_with_system_prompt(mock_litellm):
    """Test calling with system prompt."""
    handler = DefaultSamplingHandler(model="gpt-4")

    handler(
        messages=[{"role": "user", "content": "Hello"}],
        system_prompt="You are helpful",
        max_tokens=100
    )

    call_args = mock_litellm.completion.call_args
    messages = call_args[1]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "You are helpful"


def test_call_auto_selects_anthropic(mock_litellm, monkeypatch):
    """Test auto-selecting Anthropic when key available."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    for key in ["OPENAI_API_KEY", "GOOGLE_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    handler = DefaultSamplingHandler()

    handler(messages=[{"role": "user", "content": "test"}], max_tokens=100)

    call_args = mock_litellm.completion.call_args
    assert "claude" in call_args[1]["model"]


def test_call_auto_selects_openai(mock_litellm, monkeypatch):
    """Test auto-selecting OpenAI when key available."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    for key in ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    handler = DefaultSamplingHandler()

    handler(messages=[{"role": "user", "content": "test"}], max_tokens=100)

    call_args = mock_litellm.completion.call_args
    assert "gpt" in call_args[1]["model"]


def test_call_without_api_keys_raises(monkeypatch):
    """Test calling without API keys raises error."""
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    handler = DefaultSamplingHandler()

    with pytest.raises(MCPSamplingError, match="No API keys found"):
        handler(messages=[{"role": "user", "content": "test"}], max_tokens=100)


def test_call_without_litellm_raises(monkeypatch):
    """Test calling without litellm installed raises error."""
    import sys
    # Remove litellm from modules if present
    monkeypatch.setitem(sys.modules, "litellm", None)

    handler = DefaultSamplingHandler(model="gpt-4")

    with pytest.raises(MCPSamplingError, match="LiteLLM not installed"):
        handler(messages=[], max_tokens=100)


def test_call_litellm_error_wrapped(mock_litellm):
    """Test that litellm errors are wrapped in MCPSamplingError."""
    mock_litellm.completion.side_effect = Exception("API Error")
    handler = DefaultSamplingHandler(model="gpt-4")

    with pytest.raises(MCPSamplingError, match="LLM call failed"):
        handler(messages=[], max_tokens=100)


def test_call_uses_server_preferences(mock_litellm):
    """Test that server model preferences are used."""
    handler = DefaultSamplingHandler()  # No explicit model

    handler(
        messages=[{"role": "user", "content": "test"}],
        model_preferences={"model": "gpt-3.5-turbo"},
        max_tokens=100
    )

    call_args = mock_litellm.completion.call_args
    assert call_args[1]["model"] == "gpt-3.5-turbo"
