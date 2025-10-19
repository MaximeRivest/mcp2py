#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "mcp2py>=0.2.0",
# ]
# ///
"""Simplest possible example - no context manager needed.

Just load, use, done. Cleanup happens automatically.

Usage:
    ./simple_example.py
"""

from mcp2py import load
from pathlib import Path

# Use test server from repo
test_server = Path(__file__).parent.parent / "tests" / "test_server.py"

# Just load and use - cleanup is automatic
server = load(f"python {test_server}")

# Call tools
result = server.echo(message="Hello!")
print(result)

result = server.add(a=5, b=3)
print(result)

# No need to close - Python's garbage collector handles it
# Server cleans up when script exits or server goes out of scope
