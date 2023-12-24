from pathlib import Path
from typing import Any, Generator

import pytest
import yaml

import shelf.registry

testdir = Path(__file__).parent


@pytest.fixture(autouse=True)
def empty_registry() -> Generator[None, None, None]:
    """Clear out type registry between tests to avoid interference."""
    try:
        yield
    finally:
        shelf.registry._registry.clear()


@pytest.fixture(scope="session")
def fsconfig() -> dict[str, dict[str, Any]]:
    with open(testdir / "shelfconfig.yaml", "r") as f:
        return yaml.safe_load(f)
