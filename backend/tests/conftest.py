"""
pytest configuration and shared fixtures for the backend test suite.

All async tests use pytest-asyncio in "auto" mode — no need to mark
individual tests with @pytest.mark.asyncio.
"""
import pytest
import pytest_asyncio  # noqa: F401 — ensures the plugin is loaded


# ---------------------------------------------------------------------------
# pytest-asyncio configuration
# ---------------------------------------------------------------------------

# Set asyncio_mode to "auto" so every async test function is treated as an
# asyncio test without requiring the @pytest.mark.asyncio decorator.
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "asyncio: mark a test as an asyncio coroutine",
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend for anyio-based tests."""
    return "asyncio"
