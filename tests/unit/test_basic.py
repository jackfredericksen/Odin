"""Basic smoke tests for CI pipeline."""
import sys
import pytest


def test_import_odin():
    """Test that odin package can be imported."""
    import odin
    assert odin is not None


def test_python_version():
    """Verify Python version is supported."""
    assert sys.version_info >= (3, 11)


def test_basic_math():
    """Sanity check that pytest is working."""
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_async_works():
    """Test that async functionality works."""
    import asyncio
    await asyncio.sleep(0.01)
    assert True
