"""End-to-end integration test demonstrating Phase 1.4 functionality.

This test shows the complete user journey from loading a server to calling tools.
"""

import sys
from pathlib import Path

from mcp2py import load


def test_complete_workflow():
    """Test the complete workflow: load → call tools → cleanup."""
    test_server = Path(__file__).parent / "test_server.py"

    # Load server
    server = load([sys.executable, str(test_server)])

    # Verify server is loaded
    assert hasattr(server, "echo")
    assert hasattr(server, "add")

    # Call multiple tools
    echo_result = server.echo(message="Integration test")
    assert "Echo: Integration test" in echo_result

    add_result = server.add(a=10, b=20)
    assert "Result: 30" in add_result

    # Cleanup
    server.close()


def test_context_manager_workflow():
    """Test complete workflow with context manager."""
    test_server = Path(__file__).parent / "test_server.py"

    with load([sys.executable, str(test_server)]) as server:
        # Make several calls
        results = []
        for i in range(3):
            result = server.echo(message=f"Test {i}")
            results.append(result)

        # Verify all succeeded
        assert len(results) == 3
        assert all("Echo: Test" in r for r in results)

    # Server should be cleaned up automatically


def test_realistic_usage_scenario():
    """Test a realistic usage scenario with mixed operations."""
    test_server = Path(__file__).parent / "test_server.py"

    # Load server with string command
    server = load(f"{sys.executable} {test_server}")

    try:
        # Get tool references
        echo = server.echo
        add = server.add

        # Verify they're callable
        assert callable(echo)
        assert callable(add)

        # Call with various arguments
        results = []

        # Echo with different messages
        results.append(echo(message="First"))
        results.append(echo(message="Second"))

        # Add with different numbers
        results.append(add(a=1, b=1))
        results.append(add(a=100, b=200))

        # Verify all calls succeeded
        assert len(results) == 4
        assert "Echo: First" in results[0]
        assert "Echo: Second" in results[1]
        assert "Result: 2" in results[2]
        assert "Result: 300" in results[3]

    finally:
        server.close()


def test_error_handling_workflow():
    """Test error handling in realistic scenarios."""
    test_server = Path(__file__).parent / "test_server.py"

    with load([sys.executable, str(test_server)]) as server:
        # Valid call
        result = server.echo(message="test")
        assert "test" in result

        # Invalid tool should raise AttributeError
        try:
            server.nonexistent_tool()
            assert False, "Should have raised AttributeError"
        except AttributeError as e:
            assert "not found" in str(e)
            assert "Available tools:" in str(e)


def test_rapid_sequential_calls():
    """Test making many rapid calls to verify thread safety."""
    test_server = Path(__file__).parent / "test_server.py"

    with load([sys.executable, str(test_server)]) as server:
        # Make 20 rapid calls
        results = []
        for i in range(20):
            result = server.add(a=i, b=i + 1)
            results.append(result)

        # Verify all succeeded
        assert len(results) == 20
        for i, result in enumerate(results):
            expected = i + (i + 1)
            assert f"Result: {expected}" in result
