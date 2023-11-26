import json
from pathlib import Path

import shelf


def test_json_roundtrip(tmp_path: Path) -> None:
    """Test a simple data artifact JSON roundtrip."""

    def json_dump(d: dict, fname: str) -> str:
        with open(fname, "w") as f:
            json.dump(d, f)
        return fname

    def json_load(fname: str) -> dict:
        with open(fname, "r") as f:
            return json.load(f)

    shelf.register_type(dict, json_dump, json_load)

    s = shelf.Shelf(prefixes=[str(tmp_path)])

    data = {"a": 1, "b": 2}

    s.put(data, "myobj.json")
    (data2,) = s.get("myobj.json", dict)

    assert data == data2
