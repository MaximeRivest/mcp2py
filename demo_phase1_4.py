#!/usr/bin/env python3
"""Demo script showing Phase 1.4 functionality.

This demonstrates the new high-level API with the load() function.
"""

import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp2py import load


def main():
    print("🚀 mcp2py Phase 1.4 Demo - High-Level API\n")
    print("=" * 60)

    # Load the test server
    print("\n1. Loading MCP server...")
    test_server = Path(__file__).parent / "tests" / "test_server.py"
    server = load(f"python {test_server}")
    print("   ✅ Server loaded successfully!")

    # Show available tools
    print("\n2. Available tools:")
    print(f"   - server.echo (callable: {callable(server.echo)})")
    print(f"   - server.add (callable: {callable(server.add)})")

    # Call echo tool
    print("\n3. Calling server.echo(message='Hello, mcp2py!')...")
    result = server.echo(message="Hello, mcp2py!")
    print(f"   Result: {result}")

    # Call add tool
    print("\n4. Calling server.add(a=42, b=58)...")
    result = server.add(a=42, b=58)
    print(f"   Result: {result}")

    # Multiple calls
    print("\n5. Making multiple rapid calls...")
    for i in range(3):
        result = server.add(a=i, b=i * 2)
        print(f"   add({i}, {i*2}) = {result}")

    # Context manager
    print("\n6. Testing context manager...")
    with load(f"python {test_server}") as ctx_server:
        result = ctx_server.echo(message="Context manager works!")
        print(f"   Result: {result}")
    print("   ✅ Cleanup successful!")

    # Cleanup
    print("\n7. Cleaning up original server...")
    server.close()
    print("   ✅ Server closed!")

    print("\n" + "=" * 60)
    print("✨ Demo complete! Phase 1.4 is working perfectly!")
    print("\nKey features demonstrated:")
    print("  ✅ load() function with subprocess management")
    print("  ✅ Tools as Python methods")
    print("  ✅ Sync API over async implementation")
    print("  ✅ Background event loop in thread")
    print("  ✅ Context manager support")
    print("  ✅ Clean resource management")


if __name__ == "__main__":
    main()
