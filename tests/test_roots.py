"""Tests for roots normalization."""

from pathlib import Path

import pytest

from mcp2py.roots import normalize_roots


def test_normalize_none_returns_empty():
    """Test that None returns empty list."""
    result = normalize_roots(None)

    assert result == []


def test_normalize_single_string():
    """Test normalizing single string path."""
    result = normalize_roots("/tmp")

    assert len(result) == 1
    assert result[0]["uri"].startswith("file://")
    assert result[0]["uri"].endswith("/tmp")
    assert result[0]["name"] == "tmp"


def test_normalize_list_of_strings():
    """Test normalizing list of string paths."""
    result = normalize_roots(["/tmp", "/home"])

    assert len(result) == 2
    assert result[0]["name"] == "tmp"
    assert result[1]["name"] == "home"


def test_normalize_single_path():
    """Test normalizing single Path object."""
    result = normalize_roots(Path("/tmp"))

    assert len(result) == 1
    assert result[0]["uri"].startswith("file://")
    assert result[0]["name"] == "tmp"


def test_normalize_list_of_paths():
    """Test normalizing list of Path objects."""
    result = normalize_roots([Path("/tmp"), Path("/home")])

    assert len(result) == 2
    assert all(r["uri"].startswith("file://") for r in result)


def test_normalize_creates_absolute_paths():
    """Test that relative paths are converted to absolute."""
    result = normalize_roots(".")

    assert result[0]["uri"].startswith("file://")
    # Should be absolute path
    assert len(result[0]["uri"]) > len("file://.")


def test_normalize_extracts_name_from_path():
    """Test that name is extracted from last path component."""
    result = normalize_roots("/var/log/nginx")

    assert result[0]["name"] == "nginx"


def test_normalize_handles_root_directory():
    """Test normalizing root directory."""
    result = normalize_roots("/")

    assert len(result) == 1
    assert result[0]["uri"] == "file:///"
    assert result[0]["name"] == "root"  # Default name for /


def test_normalize_result_structure():
    """Test that result has correct structure."""
    result = normalize_roots("/tmp")

    assert len(result) == 1
    assert "uri" in result[0]
    assert "name" in result[0]
    assert isinstance(result[0]["uri"], str)
    assert isinstance(result[0]["name"], str)
