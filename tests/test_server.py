#!/usr/bin/env python3
"""Simple test MCP server for testing transport layer."""

import asyncio
import json
import sys


async def main() -> None:
    """Run a simple echo server for testing."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break

        # Parse incoming message
        try:
            msg = json.loads(line.decode("utf-8"))

            # Echo back with same ID
            response = {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {"echo": msg.get("method", "unknown")},
            }

            # Write response
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            sys.stderr.write("Invalid JSON\n")
            sys.stderr.flush()


if __name__ == "__main__":
    asyncio.run(main())
