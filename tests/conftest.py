from pathlib import Path
from typing import Generator

import pytest

import shelf.registry

testdir = Path(__file__).parent


@pytest.fixture(autouse=True)
def empty_registry() -> Generator[None, None, None]:
    """Clear out type registry between tests to avoid interference."""
    try:
        yield
    finally:
        shelf.registry._registry.clear()
