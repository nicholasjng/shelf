import contextlib
import os
import tempfile
from os import PathLike
from pathlib import Path
from typing import Any, Literal, TypeVar

from fsspec import AbstractFileSystem, filesystem
from fsspec.utils import get_protocol

import shelf.registry as registry
from shelf.util import is_fully_qualified

T = TypeVar("T")


def load_config(filename: str | Path) -> dict[str, Any]:
    def get_project_root() -> Path:
        """
        Returns project root if currently in a project (sub-)folder,
        otherwise the current directory.
        """
        cwd = Path.cwd()
        for p in (cwd, *cwd.parents):
            if (p / "setup.py").exists() or (p / "pyproject.toml").exists():
                return p
        return cwd

    config: dict[str, Any] = {}

    for loc in [Path.home(), get_project_root()]:
        if (pp := loc / filename).exists():
            with open(pp, "r") as f:
                import yaml

                config = yaml.safe_load(f)
    return config


class Shelf:
    def __init__(
        self,
        prefix: str | os.PathLike[str] = "",
        cache_dir: str | PathLike[str] | None = None,
        cache_type: Literal["blockcache", "filecache", "simplecache"] = "filecache",
        fsconfig: dict[str, dict[str, Any]] | None = None,
    ):
        self.prefix = str(prefix)

        self.cache_type = cache_type
        self.cache_dir = cache_dir

        # config object holding storage options for file systems
        self.fsconfig = fsconfig or {}

    def get(self, rpath: str, expected_type: type[T]) -> T:
        if not is_fully_qualified(rpath):
            rpath = self.prefix + rpath

        # load machinery early, so that we do not download
        # if the type is not registered.
        serde = registry.lookup(expected_type)
        protocol = get_protocol(rpath)

        # file system-specific options.
        config = self.fsconfig.get(protocol, {})
        storage_options = config.get("storage", {})

        if self.cache_dir is not None:
            proto = self.cache_type
            kwargs = {
                "target_protocol": protocol,
                "target_options": storage_options,
                "cache_storage": self.cache_dir,
            }
        else:
            proto = protocol
            kwargs = storage_options

        fs: AbstractFileSystem = filesystem(proto, **kwargs)

        download_options = config.get("download", {})

        with contextlib.ExitStack() as stack:
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory())
            stack.enter_context(contextlib.chdir(tmpdir))

            # trailing slash tells fsspec to download files into `lpath`
            lpath = tmpdir + os.sep
            fs.get(rpath, lpath, **download_options)

            # TODO: Find a way to pass files in expected order
            filenames = [p.name for p in Path(tmpdir).iterdir() if p.is_file()]
            obj: T = serde.deserializer(*filenames)

        return obj

    def put(self, obj: T, rpath: str) -> None:
        # load machinery early, so that we do not download
        # if the type is not registered.
        serde = registry.lookup(type(obj))

        if not is_fully_qualified(rpath):
            rpath = self.prefix + rpath

        protocol = get_protocol(rpath)

        # file system-specific options.
        fsconfig = self.fsconfig.get(protocol, {})
        storage_options = fsconfig.get("storage", {})

        if self.cache_dir is not None:
            proto = self.cache_type
            kwargs = {
                "target_protocol": protocol,
                "target_options": storage_options,
                "cache_storage": self.cache_dir,
            }
        else:
            proto = protocol
            kwargs = storage_options

        fs: AbstractFileSystem = filesystem(proto, **kwargs)

        with contextlib.ExitStack() as stack:
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory())
            # chdir into the temporary to be able to work with filenames only
            stack.enter_context(contextlib.chdir(tmpdir))
            # TODO: What about multiple lpaths?
            lpath = serde.serializer(obj)

            upload_options = fsconfig.get("upload", {})
            fs.put(lpath, rpath, **upload_options)

        return fs.info(rpath)
