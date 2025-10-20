"""Elicitation handler for MCP servers that request user input.

When a server needs user input (e.g., confirmation, preferences), mcp2py can
automatically prompt the user via terminal.
"""

from typing import Any, Callable

from mcp2py.exceptions import MCPElicitationError


class DefaultElicitationHandler:
    """Terminal-based user input with nice formatting.

    Prompts the user for input based on the schema provided by the server.

    Example:
        >>> handler = DefaultElicitationHandler()
        >>> # Use with load()
        >>> from mcp2py import load
        >>> server = load("npx my-server", on_elicitation=handler)
    """

    def __init__(self, defaults: dict[str, Any] | None = None):
        """Initialize elicitation handler.

        Args:
            defaults: Default values for specific prompts
        """
        self.defaults = defaults or {}

    def __call__(self, message: str, schema: dict[str, Any]) -> Any:
        """Prompt user for input.

        Args:
            message: Message to display to user
            schema: JSON Schema describing expected input

        Returns:
            User's input, parsed according to schema

        Raises:
            MCPElicitationError: If input fails or is invalid

        Example:
            >>> handler = DefaultElicitationHandler()
            >>> # In real use, would prompt user
            >>> # For tests, we mock input()
        """
        print(f"\n┌{'─' * 60}┐")
        print(f"│ 🔔 Server needs your input{' ' * 34}│")
        print(f"├{'─' * 60}┤")
        print(f"│ {message[:58].ljust(58)} │")
        print(f"└{'─' * 60}┘\n")

        schema_type = schema.get("type", "string")

        try:
            if schema_type == "boolean":
                return self._prompt_boolean(schema)
            elif schema_type == "string":
                return self._prompt_string(schema)
            elif schema_type == "integer":
                return self._prompt_integer(schema)
            elif schema_type == "number":
                return self._prompt_number(schema)
            elif schema_type == "object":
                return self._prompt_object(schema)
            else:
                # Default to string input
                return self._prompt_string(schema)
        except (ValueError, KeyboardInterrupt) as e:
            raise MCPElicitationError(f"Input failed: {e}") from e

    def _prompt_boolean(self, schema: dict[str, Any]) -> bool:
        """Prompt for boolean value.

        Args:
            schema: Schema definition

        Returns:
            Boolean value
        """
        description = schema.get("description", "")
        prompt = f"{description} " if description else ""
        prompt += "(y/n): "

        value = input(prompt).lower().strip()
        return value in ["y", "yes", "true", "1"]

    def _prompt_string(self, schema: dict[str, Any]) -> str:
        """Prompt for string value.

        Args:
            schema: Schema definition

        Returns:
            String value
        """
        description = schema.get("description", "")
        prompt = f"{description}: " if description else "> "

        return input(prompt).strip()

    def _prompt_integer(self, schema: dict[str, Any]) -> int:
        """Prompt for integer value.

        Args:
            schema: Schema definition

        Returns:
            Integer value
        """
        description = schema.get("description", "")
        prompt = f"{description} (integer): " if description else "Enter number: "

        value = input(prompt).strip()
        return int(value)

    def _prompt_number(self, schema: dict[str, Any]) -> float:
        """Prompt for number value.

        Args:
            schema: Schema definition

        Returns:
            Float value
        """
        description = schema.get("description", "")
        prompt = f"{description} (number): " if description else "Enter number: "

        value = input(prompt).strip()
        return float(value)

    def _prompt_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Prompt for object value (multiple fields).

        Args:
            schema: Schema definition

        Returns:
            Dictionary of values
        """
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        result = {}

        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required
            prop_type = prop_schema.get("type", "string")
            description = prop_schema.get("description", prop_name)

            prompt_text = f"  {description}"
            if not is_required:
                prompt_text += " (optional)"
            prompt_text += ": "

            # Check for default value
            if prop_name in self.defaults:
                result[prop_name] = self.defaults[prop_name]
                print(f"{prompt_text}[using default: {result[prop_name]}]")
                continue

            # Prompt based on type
            try:
                if prop_type == "boolean":
                    value = input(f"{prompt_text}(y/n) ").lower().strip()
                    if value:
                        result[prop_name] = value in ["y", "yes", "true", "1"]
                    elif is_required:
                        raise ValueError(f"Required field '{prop_name}' cannot be empty")
                elif prop_type == "integer":
                    value = input(prompt_text).strip()
                    if value:
                        result[prop_name] = int(value)
                    elif is_required:
                        raise ValueError(f"Required field '{prop_name}' cannot be empty")
                elif prop_type == "number":
                    value = input(prompt_text).strip()
                    if value:
                        result[prop_name] = float(value)
                    elif is_required:
                        raise ValueError(f"Required field '{prop_name}' cannot be empty")
                else:  # string
                    value = input(prompt_text).strip()
                    if value:
                        result[prop_name] = value
                    elif is_required:
                        raise ValueError(f"Required field '{prop_name}' cannot be empty")
            except ValueError as e:
                if is_required:
                    raise
                # Optional field, skip if invalid

        return result


# Type for custom elicitation handlers
ElicitationHandler = Callable[[str, dict[str, Any]], Any]
