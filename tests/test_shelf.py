import json
import os
from pathlib import Path

import shelf


def test_json_roundtrip(tmp_path: Path) -> None:
    """Test a simple data artifact JSON roundtrip."""

    def json_dump(d: dict, tmpdir: str) -> str:
        fname = os.path.join(tmpdir, "dump.json")
        with open(fname, "w") as f:
            json.dump(d, f)
        return fname

    def json_load(fname: str) -> dict:
        with open(fname, "r") as f:
            return json.load(f)

    shelf.register_type(dict, json_dump, json_load)

    s = shelf.Shelf(prefix=tmp_path)

    data = {"a": 1, "b": 2}

    s.put(data, "myobj.json")
    data2 = s.get("myobj.json", dict)

    assert data == data2


def test_multifile_artifact(tmp_path: Path, fsconfig: dict) -> None:
    """
    Test a dict artifact JSON roundtrip with the dict serialized into two different files.

    No nested directories, only multiple filenames.
    """

    def json_dump(d: dict, tmpdir: str) -> tuple[str, ...]:
        d1, d2 = {"a": d["a"]}, {"b": d["b"]}
        fnames = []
        for i, d in enumerate((d1, d2)):
            fname = os.path.join(tmpdir, f"dump{i}.json")
            fnames.append(fname)
            with open(fname, "w") as f:
                json.dump(d, f)
        return tuple(fnames)

    def json_load(fnames: tuple[str, str]) -> dict:
        d: dict = {}
        for fname in fnames:
            with open(fname, "r") as f:
                d |= json.load(f)
        return d

    shelf.register_type(dict, json_dump, json_load)

    s = shelf.Shelf(prefix=tmp_path, fsconfig=fsconfig)

    data = {"a": 1, "b": 2}

    s.put(data, "myobj")
    data2 = s.get("myobj", dict)

    assert data == data2
