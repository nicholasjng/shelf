from typing import Generator

import pytest

from shelf.registry import _registry


@pytest.fixture(autouse=True)
def empty_registry() -> Generator[None, None, None]:
    """Clear out type registry between tests to avoid interference."""
    try:
        yield
    finally:
        _registry.clear()
