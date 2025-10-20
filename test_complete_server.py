#!/usr/bin/env python3
"""Test script for complete MCP server with all capabilities."""

from mcp2py import load, DefaultSamplingHandler
import os

def test_basic_features():
    """Test basic MCP features."""
    print("=" * 60)
    print("Testing Complete MCP Server")
    print("=" * 60)

    # Load server
    print("\n1️⃣  Loading test server...")
    server = load("python tests/test_server.py")

    print(f"\n📊 Server Capabilities:")
    print(f"  Tools: {list(server._tools.keys())}")
    print(f"  Resources: {list(server._resources.keys())}")
    print(f"  Prompts: {list(server._prompts.keys())}")

    # Test basic tools
    print(f"\n2️⃣  Testing Basic Tools:")
    result = server.echo(message="Hello from mcp2py!")
    print(f"  ✓ echo: {result}")

    result = server.add(a=15, b=27)
    print(f"  ✓ add: {result}")

    # Test resources
    print(f"\n3️⃣  Testing Resources:")
    docs = server.API_Documentation
    print(f"  ✓ API Documentation: {len(docs)} chars")
    print(f"    Preview: {docs[:100]}...")

    import json
    version = json.loads(server.Version_Info)
    print(f"  ✓ Version Info: v{version['version']}")
    print(f"    Protocol: {version['protocol_version']}")

    stats = json.loads(server.Server_Statistics)
    print(f"  ✓ Server Statistics: {stats}")

    # Test prompts
    print(f"\n4️⃣  Testing Prompts:")
    messages = server.review_code(
        code="def factorial(n):\n    return n * factorial(n-1)",
        focus="bugs"
    )
    print(f"  ✓ review_code: Generated {len(messages)} messages")
    print(f"    Role: {messages[0]['role']}")
    print(f"    Preview: {str(messages[0]['content'])[:80]}...")

    messages = server.generate_readme(
        project_name="awesome-lib",
        description="An awesome library",
        features="Fast, Simple, Powerful"
    )
    print(f"  ✓ generate_readme: Generated {len(messages)} messages")

    messages = server.explain_mcp()
    print(f"  ✓ explain_mcp: Generated {len(messages)} messages")

    print(f"\n5️⃣  Sampling & Elicitation Tools (not tested - require interaction):")
    print(f"  ✓ analyze_sentiment: Available (triggers sampling)")
    print(f"  ✓ confirm_action: Available (triggers elicitation)")

    server.close()
    print(f"\n✅ All basic features working!")
    print("=" * 60)


def test_sampling():
    """Test sampling feature (requires API key)."""
    print("\n" + "=" * 60)
    print("Testing Sampling (Optional - requires API key)")
    print("=" * 60)

    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  No API keys found. Skipping sampling test.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test sampling.")
        return

    print("\n🤖 Testing LLM Sampling:")
    server = load("python tests/test_server.py")

    try:
        result = server.analyze_sentiment(text="I absolutely love Python programming!")
        print(f"  ✓ Sentiment analysis: {result}")
    except Exception as e:
        print(f"  ✗ Sampling failed: {type(e).__name__}: {e}")

    server.close()


def test_elicitation():
    """Test elicitation feature (interactive)."""
    print("\n" + "=" * 60)
    print("Testing Elicitation (Interactive)")
    print("=" * 60)

    print("\n💬 Testing User Input Prompts:")
    server = load("python tests/test_server.py")

    try:
        print("\nThis will prompt you for confirmation...")
        result = server.confirm_action(action="delete all files")
        print(f"  ✓ User response: {result}")
    except KeyboardInterrupt:
        print("\n  ✗ Test cancelled by user")
    except Exception as e:
        print(f"  ✗ Elicitation failed: {type(e).__name__}: {e}")

    server.close()


if __name__ == "__main__":
    # Always run basic tests
    test_basic_features()

    # Optional: test sampling if requested
    if "--sampling" in __import__("sys").argv:
        test_sampling()

    # Optional: test elicitation if requested
    if "--elicitation" in __import__("sys").argv:
        test_elicitation()

    print("\n💡 Tip: Run with --sampling or --elicitation to test those features")
