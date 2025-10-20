"""Roots configuration for MCP servers.

Roots tell the server which directories to focus on for file operations.
"""

from pathlib import Path
from typing import Any


def normalize_roots(roots: str | list[str] | Path | list[Path] | None) -> list[dict[str, str]]:
    """Normalize roots to MCP format.

    Converts various root specifications into the format expected by MCP servers.

    Args:
        roots: Single path, list of paths, or None

    Returns:
        List of root dictionaries with 'uri' and 'name' keys

    Example:
        >>> normalize_roots("/tmp")
        [{'uri': 'file:///tmp', 'name': 'tmp'}]
        >>> normalize_roots(["/tmp", "/home"])
        [{'uri': 'file:///tmp', 'name': 'tmp'}, {'uri': 'file:///home', 'name': 'home'}]
        >>> normalize_roots(None)
        []
    """
    if roots is None:
        return []

    # Convert single item to list
    if isinstance(roots, (str, Path)):
        roots = [roots]

    result: list[dict[str, str]] = []
    for root in roots:
        # Convert to Path for consistent handling
        path = Path(root) if isinstance(root, str) else root

        # Get absolute path
        abs_path = path.absolute()

        # Create file:// URI
        uri = abs_path.as_uri()

        # Use last component as name
        name = abs_path.name or "root"

        result.append({"uri": uri, "name": name})

    return result
