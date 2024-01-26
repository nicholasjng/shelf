import json
from pathlib import Path

from fsspec.implementations.local import LocalFileSystem

import shelf


def test_json_roundtrip(tmp_path: Path) -> None:
    """Test a simple data artifact JSON roundtrip."""

    def json_dump(d: dict, ctx: shelf.Context) -> None:
        fp = ctx.file("dump.json", mode="w")
        json.dump(d, fp)

    def json_load(ctx: shelf.Context) -> dict:
        (fname,) = ctx.filenames
        fp = ctx.file(fname, mode="r")
        return json.load(fp)

    shelf.register_type(dict, json_dump, json_load)

    shlf = shelf.Shelf()

    data = {"a": 1, "b": 2}

    rpath = f"file://{tmp_path}/myobj.json"

    shlf.put(data, rpath)
    fs = LocalFileSystem()
    assert fs.exists(rpath)
    assert fs.size(rpath) > 0
    data2 = shlf.get(rpath, dict)

    assert data == data2


def test_multifile_artifact(tmp_path: Path) -> None:
    """
    Test a dict artifact JSON roundtrip with the dict serialized into two different files.

    No nested directories, only multiple filenames.
    """

    def json_dump(d: dict, ctx: shelf.Context) -> None:
        d1, d2 = {"a": d["a"]}, {"b": d["b"]}
        for i, d in enumerate((d1, d2)):
            fp = ctx.file(f"dump{i}.json", mode="w")
            json.dump(d, fp)

    def json_load(ctx: shelf.Context) -> dict:
        d: dict = {}
        for fname in ctx.filenames:
            with open(fname, "r") as f:
                d |= json.load(f)
        return d

    shelf.register_type(dict, json_dump, json_load)

    shlf = shelf.Shelf()
    storage_options = {"auto_mkdir": True}

    data = {"a": 1, "b": 2}

    shlf.put(data, f"file://{tmp_path}/myobj", storage_options=storage_options)
    datanew = shlf.get(f"file://{tmp_path}/myobj", dict, storage_options=storage_options)

    assert data == datanew
