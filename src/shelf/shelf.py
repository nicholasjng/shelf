from typing import Any, Sequence

from .registry import registry

class Shelf:

    def __init__(self, prefixes: Sequence[str]):
        self.prefixes = tuple(prefixes)
        self._registry = registry

    @property
    def registry(self):
        return self._registry

    def get(self, prefix: str, expected_type: type) -> Any:
        pass

    def put(self, artefact: Any, destination: str) -> None:
        pass
