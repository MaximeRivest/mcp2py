"""Sampling handler for MCP servers that request LLM completions.

When a server needs LLM help (e.g., to generate content), mcp2py can automatically
handle these requests using LiteLLM.
"""

import os
from typing import Any, Callable

from mcp2py.exceptions import MCPSamplingError


class DefaultSamplingHandler:
    """Automatic LLM sampling using LiteLLM.

    Detects API keys from environment and calls appropriate LLM provider.
    Supports all providers that LiteLLM supports (OpenAI, Anthropic, Google, etc.).

    Example:
        >>> import os
        >>> os.environ["OPENAI_API_KEY"] = "sk-test"
        >>> handler = DefaultSamplingHandler()
        >>> handler.can_handle()
        True
        >>> # Use with load()
        >>> from mcp2py import load
        >>> server = load("npx my-server", on_sampling=handler)
    """

    def __init__(self, model: str | None = None):
        """Initialize sampling handler.

        Args:
            model: Model to use (e.g., "claude-3-5-sonnet-20241022", "gpt-4o-mini")
                  If None, auto-detects based on available API keys
        """
        self.model = model

    def can_handle(self) -> bool:
        """Check if handler can make LLM calls.

        Returns:
            True if API keys are available
        """
        if self.model:
            return True

        # Check for common API keys
        return bool(
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )

    def __call__(
        self,
        messages: list[dict[str, Any]],
        model_preferences: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
    ) -> str:
        """Handle sampling request from server.

        Args:
            messages: List of messages for the LLM
            model_preferences: Server's model preferences (hints)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text from LLM

        Raises:
            MCPSamplingError: If sampling fails

        Example:
            >>> handler = DefaultSamplingHandler(model="gpt-4o-mini")
            >>> result = handler(
            ...     messages=[{"role": "user", "content": "Hello!"}],
            ...     max_tokens=100
            ... )
            >>> isinstance(result, str)
            True
        """
        try:
            import litellm
        except ImportError:
            raise MCPSamplingError(
                "LiteLLM not installed. Install with: pip install litellm"
            )

        # Determine model to use
        model = self._select_model(model_preferences)

        # Build request
        request_messages = messages.copy()
        if system_prompt:
            request_messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            response = litellm.completion(
                model=model, messages=request_messages, max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise MCPSamplingError(f"LLM call failed: {e}") from e

    def _select_model(self, preferences: dict[str, Any] | None) -> str:
        """Select which model to use.

        Args:
            preferences: Server's model preferences

        Returns:
            Model identifier for LiteLLM
        """
        # Use explicit model if set
        if self.model:
            return self.model

        # Try to use server's preferred model
        if preferences and "model" in preferences:
            return preferences["model"]

        # Auto-detect based on available API keys
        if os.getenv("ANTHROPIC_API_KEY"):
            return "claude-3-5-sonnet-20241022"
        elif os.getenv("OPENAI_API_KEY"):
            return "gpt-4o-mini"
        elif os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
            return "gemini/gemini-pro"
        else:
            raise MCPSamplingError(
                "No API keys found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
            )


# Type for custom sampling handlers
SamplingHandler = Callable[
    [list[dict[str, Any]], dict[str, Any] | None, str | None, int], str
]
