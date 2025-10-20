"""Server registry for mcp2py.

Allows registering commonly-used servers with friendly names, stored in
~/.config/mcp2py/servers.json
"""

import json
from pathlib import Path
from typing import Any

from mcp2py.exceptions import MCPConfigError


def get_registry_path() -> Path:
    """Get path to registry file.

    Returns:
        Path to ~/.config/mcp2py/servers.json
    """
    config_dir = Path.home() / ".config" / "mcp2py"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "servers.json"


def load_registry() -> dict[str, str]:
    """Load registry from disk.

    Returns:
        Dictionary mapping server names to commands

    Example:
        >>> registry = load_registry()
        >>> isinstance(registry, dict)
        True
    """
    registry_path = get_registry_path()

    if not registry_path.exists():
        return {}

    try:
        with open(registry_path, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise MCPConfigError("Registry file is corrupted (not a dict)")
            return data
    except json.JSONDecodeError as e:
        raise MCPConfigError(f"Registry file is corrupted: {e}") from e
    except Exception as e:
        raise MCPConfigError(f"Failed to load registry: {e}") from e


def save_registry(registry: dict[str, str]) -> None:
    """Save registry to disk.

    Args:
        registry: Dictionary mapping server names to commands

    Raises:
        MCPConfigError: If save fails

    Example:
        >>> save_registry({"weather": "npx weather-server"})
    """
    registry_path = get_registry_path()

    try:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        raise MCPConfigError(f"Failed to save registry: {e}") from e


def register(**servers: str) -> None:
    """Register MCP servers with friendly names.

    Args:
        **servers: Keyword arguments mapping names to commands

    Raises:
        MCPConfigError: If registration fails
        ValueError: If invalid arguments provided

    Example:
        >>> register(
        ...     weather="npx -y @h1deya/mcp-server-weather",
        ...     filesystem="npx -y @modelcontextprotocol/server-filesystem /tmp"
        ... )
        >>> # Now you can use: load("weather")
    """
    if not servers:
        raise ValueError("No servers provided")

    # Validate all are strings
    for name, command in servers.items():
        if not isinstance(command, str):
            raise ValueError(f"Command for '{name}' must be a string, got {type(command)}")

    # Load existing registry
    registry = load_registry()

    # Update with new servers
    registry.update(servers)

    # Save back
    save_registry(registry)


def unregister(*names: str) -> None:
    """Unregister servers by name.

    Args:
        *names: Server names to remove

    Raises:
        MCPConfigError: If unregister fails
        ValueError: If no names provided

    Example:
        >>> unregister("weather", "filesystem")
    """
    if not names:
        raise ValueError("No server names provided")

    registry = load_registry()

    for name in names:
        if name in registry:
            del registry[name]

    save_registry(registry)


def list_registered() -> dict[str, str]:
    """List all registered servers.

    Returns:
        Dictionary of registered servers

    Example:
        >>> servers = list_registered()
        >>> isinstance(servers, dict)
        True
    """
    return load_registry()


def get_command(name: str) -> str | None:
    """Get command for a registered server.

    Args:
        name: Server name

    Returns:
        Command string, or None if not found

    Example:
        >>> register(weather="npx weather-server")
        >>> get_command("weather")
        'npx weather-server'
        >>> get_command("nonexistent")
    """
    registry = load_registry()
    return registry.get(name)
