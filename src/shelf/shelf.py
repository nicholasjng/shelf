import tempfile
from pathlib import Path
from typing import Any, Sequence

import yaml
from fsspec import AbstractFileSystem, get_filesystem_class
from fsspec.utils import get_protocol

import shelf.registry as registry


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
                config = yaml.safe_load(f)
    return config


class Shelf:
    def __init__(self, prefixes: Sequence[str], configfile: str | Path = ".shelf.yaml"):
        self.prefixes = tuple(prefixes)
        self.config = load_config(configfile)
        # TODO: Local mirror in place of tempdir

    def get(self, path: str, expected_type: type) -> Any:
        objs = []
        for prefix in self.prefixes:
            with tempfile.NamedTemporaryFile() as fp:
                lpath = fp.name
                rpath = prefix + "/" + path

                # load machinery here, so that we do not download
                # if the type is not registered.
                serde = registry.lookup(expected_type)

                protocol = get_protocol(rpath)

                # file system-specific options.
                fsconfig = self.config.get(protocol, {})
                storage_options = fsconfig.get("storage", {})
                fs: AbstractFileSystem = get_filesystem_class(protocol)(**storage_options)

                download_options = fsconfig.get("download", {})
                fs.get(rpath, lpath, **download_options)

                obj = serde.deserializer(lpath)
                objs.append(obj)

        return tuple(objs)

    def put(self, obj: Any, path: str) -> tuple:
        infos = []
        for prefix in self.prefixes:
            with tempfile.NamedTemporaryFile() as fp:
                serde = registry.lookup(type(obj))

                # TODO: What about multiple lpaths?
                lpath = serde.serializer(obj, fp.name)
                rpath = prefix + "/" + path

                protocol = get_protocol(rpath)

                # file system-specific options.
                fsconfig = self.config.get(protocol, {})
                storage_options = fsconfig.get("storage", {})
                fs: AbstractFileSystem = get_filesystem_class(protocol)(**storage_options)

                upload_options = fsconfig.get("upload", {})
                fs.put(lpath, rpath, **upload_options)

                infos.append(fs.info(rpath))

        return tuple(infos)
