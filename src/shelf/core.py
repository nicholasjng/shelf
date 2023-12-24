from __future__ import annotations

import contextlib
import os
import tempfile
from os import PathLike
from typing import Any, Literal, TypeVar

from fsspec import AbstractFileSystem, filesystem
from fsspec.utils import get_protocol

import shelf.registry
from shelf.util import is_fully_qualified, with_trailing_sep

T = TypeVar("T")


class Shelf:
    def __init__(
        self,
        prefix: str | os.PathLike[str] = "",
        cache_dir: str | PathLike[str] | None = None,
        cache_type: Literal["blockcache", "filecache", "simplecache"] = "filecache",
        fsconfig: dict[str, dict[str, Any]] | None = None,
        configfile: str | PathLike[str] | None = None,
    ):
        self.prefix = str(prefix)

        self.cache_type = cache_type
        self.cache_dir = cache_dir

        # config object holding storage options for file systems
        # TODO: Validate schema for inputs
        if configfile and not fsconfig:
            import yaml

            with open(configfile, "r") as f:
                self.fsconfig = yaml.safe_load(f)
        else:
            self.fsconfig = fsconfig or {}

    def get(self, rpath: str, expected_type: type[T]) -> T:
        # load machinery early, so that we do not download
        # if the type is not registered.
        serde = shelf.registry.lookup(expected_type)

        if not is_fully_qualified(rpath):
            rpath = os.path.join(self.prefix, rpath)

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

        try:
            rfiles = fs.ls(rpath, detail=False)
        # some file systems (e.g. local) don't allow filenames in `ls`
        except NotADirectoryError:
            rfiles = [fs.info(rpath)["name"]]

        if not rfiles:
            raise FileNotFoundError(rpath)

        with contextlib.ExitStack() as stack:
            tmpdir = stack.enter_context(tempfile.TemporaryDirectory())
            # TODO: Push a unique directory (e.g. checksum) in front to
            #  create a directory

            # explicit file lists have the side effect that remote subdirectory structures
            # are flattened.
            lfiles = [os.path.join(tmpdir, os.path.basename(f)) for f in rfiles]

            download_options = config.get("download", {})
            fs.get(rfiles, lfiles, **download_options)

            # TODO: Support deserializer interfaces taking unraveled tuples, i.e. filenames
            #  as arguments in the multifile case
            lpath: str | tuple[str, ...]
            if len(lfiles) == 1:
                lpath = lfiles[0]
            else:
                lpath = tuple(lfiles)

            obj: T = serde.deserializer(lpath)

        return obj

    def put(self, obj: T, rpath: str) -> None:
        # load machinery early, so that we do not download
        # if the type is not registered.
        serde = shelf.registry.lookup(type(obj))

        if not is_fully_qualified(rpath):
            rpath = os.path.join(self.prefix, rpath)

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
            lpath = serde.serializer(obj, tmpdir)

            recursive = isinstance(lpath, (list, tuple))
            if recursive:
                # signals fsspec to put all files into rpath directory
                rpath = with_trailing_sep(rpath)

            upload_options = fsconfig.get("upload", {})
            # TODO: Construct explicit lists always to hit the fast path of fs.put()
            fs.put(lpath, rpath, recursive=recursive, **upload_options)

        return fs.info(rpath)
