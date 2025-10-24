"""Unit tests for the hello module."""

import pytest

from src.main import sayHello


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Alice", "Hello, Alice!"),
        ("Bob", "Hello, Bob!"),
    ],
)
def test_greet_various_names(name, expected):
    """Test greet with various input names."""
    assert sayHello(name) == expected
