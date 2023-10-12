from typing import Any


class Shelf:
    def get(self, prefix: str, expected_type: type) -> Any:
        pass

    def put(self, artefact: Any, destination: str) -> None:
        pass
