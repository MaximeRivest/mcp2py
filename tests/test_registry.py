"""Tests for server registry."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp2py import MCPConfigError
from mcp2py.registry import (
    get_registry_path,
    load_registry,
    save_registry,
    register,
    unregister,
    list_registered,
    get_command,
)


@pytest.fixture
def temp_registry(tmp_path, monkeypatch):
    """Create temporary registry file for testing."""
    config_dir = tmp_path / ".config" / "mcp2py"
    config_dir.mkdir(parents=True, exist_ok=True)
    registry_file = config_dir / "servers.json"

    # Mock get_registry_path to use temp directory
    monkeypatch.setattr(
        "mcp2py.registry.get_registry_path", lambda: registry_file
    )

    return registry_file


def test_get_registry_path_creates_directory(tmp_path, monkeypatch):
    """Test that registry path creation makes parent directories."""
    config_dir = tmp_path / ".config" / "mcp2py"
    monkeypatch.setattr(
        "mcp2py.registry.Path.home", lambda: tmp_path
    )

    path = get_registry_path()

    assert path.parent.exists()
    assert path.parent == config_dir


def test_load_registry_empty_when_no_file(temp_registry):
    """Test that loading non-existent registry returns empty dict."""
    registry = load_registry()

    assert registry == {}


def test_save_and_load_registry(temp_registry):
    """Test saving and loading registry."""
    test_registry = {
        "weather": "npx weather-server",
        "fs": "npx filesystem-server /tmp"
    }

    save_registry(test_registry)
    loaded = load_registry()

    assert loaded == test_registry


def test_register_servers(temp_registry):
    """Test registering multiple servers."""
    register(
        weather="npx weather-server",
        filesystem="npx filesystem-server /tmp"
    )

    registry = load_registry()

    assert registry["weather"] == "npx weather-server"
    assert registry["filesystem"] == "npx filesystem-server /tmp"


def test_register_updates_existing(temp_registry):
    """Test that register updates existing entries."""
    register(weather="npx old-weather")
    register(weather="npx new-weather")

    registry = load_registry()

    assert registry["weather"] == "npx new-weather"


def test_register_requires_servers():
    """Test that register requires at least one server."""
    with pytest.raises(ValueError, match="No servers provided"):
        register()


def test_register_validates_string_commands():
    """Test that register validates command types."""
    with pytest.raises(ValueError, match="must be a string"):
        register(invalid=123)  # type: ignore


def test_unregister_servers(temp_registry):
    """Test unregistering servers."""
    register(weather="npx weather", fs="npx fs")

    unregister("weather")

    registry = load_registry()
    assert "weather" not in registry
    assert "fs" in registry


def test_unregister_multiple(temp_registry):
    """Test unregistering multiple servers at once."""
    register(a="cmd1", b="cmd2", c="cmd3")

    unregister("a", "c")

    registry = load_registry()
    assert "a" not in registry
    assert "b" in registry
    assert "c" not in registry


def test_unregister_requires_names():
    """Test that unregister requires at least one name."""
    with pytest.raises(ValueError, match="No server names provided"):
        unregister()


def test_list_registered(temp_registry):
    """Test listing registered servers."""
    test_servers = {"weather": "npx weather", "fs": "npx fs"}
    register(**test_servers)

    listed = list_registered()

    assert listed == test_servers


def test_get_command_existing(temp_registry):
    """Test getting command for registered server."""
    register(weather="npx weather-server")

    cmd = get_command("weather")

    assert cmd == "npx weather-server"


def test_get_command_nonexistent(temp_registry):
    """Test getting command for non-existent server."""
    cmd = get_command("nonexistent")

    assert cmd is None


def test_corrupted_registry_raises_error(temp_registry):
    """Test that corrupted registry file raises MCPConfigError."""
    # Write invalid JSON
    temp_registry.write_text("not valid json {")

    with pytest.raises(MCPConfigError, match="corrupted"):
        load_registry()


def test_non_dict_registry_raises_error(temp_registry):
    """Test that non-dict registry raises MCPConfigError."""
    # Write valid JSON but not a dict
    temp_registry.write_text('["not", "a", "dict"]')

    with pytest.raises(MCPConfigError, match="not a dict"):
        load_registry()
