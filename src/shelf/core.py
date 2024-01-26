from __future__ import annotations

import os
import shutil
import tempfile
import weakref
from typing import Any, TypeVar

from fsspec.utils import stringify_path

import shelf.registry
from shelf.types import CacheOptions, Context
from shelf.util import filesystem_from_uri, with_trailing_sep

T = TypeVar("T")


class Shelf:
    def __init__(self, cache_options: CacheOptions | None = None):
        self.cache_options = cache_options

        _tempdir = tempfile.mkdtemp()
        self._tempdir = _tempdir
        weakref.finalize(self, self._cleanup_tempdir, _tempdir)

    @property
    def tempdir(self) -> str:
        return self._tempdir

    @staticmethod
    def _cleanup_tempdir(tempdir: str) -> None:
        # TODO: Use TemporaryDirectory's builtin finalizer?
        shutil.rmtree(tempdir, ignore_errors=True)

    def get(
        self,
        rpath: str | os.PathLike[str],
        expected_type: type[T],
        storage_options: dict[str, Any] | None = None,
        download_options: dict[str, Any] | None = None,
    ) -> T:
        # load machinery early, so we don't download if the type is not registered.
        serde = shelf.registry.lookup(expected_type)

        rpath = stringify_path(rpath)

        fs = filesystem_from_uri(rpath, self.cache_options, storage_options)

        rfiles: list[str]
        try:
            rfiles = fs.ls(rpath, detail=False)
        # some file systems (e.g. local) don't allow filenames in `ls`
        except NotADirectoryError:
            rfiles = [fs.info(rpath)["name"]]

        if not rfiles:
            raise FileNotFoundError(rpath)

        # explicit file lists have the side effect that remote subdirectory structures
        # are flattened.
        lfiles = [os.path.join(self.tempdir, os.path.basename(f)) for f in rfiles]
        fs.get(rfiles, lfiles, **(download_options or {}))

        # TODO: For more secure access, only allow lfiles as file descriptors
        with Context(self.tempdir, filenames=lfiles) as ctx:
            obj = serde.deserializer(ctx)

        return obj

    def put(
        self,
        obj: T,
        rpath: str | os.PathLike[str],
        storage_options: dict[str, Any] | None = None,
        upload_options: dict[str, Any] | None = None,
    ) -> None:
        # load machinery early, so we don't download if the type is not registered.
        objtype: type[T] = type(obj)

        serde = shelf.registry.lookup(objtype)

        rpath = stringify_path(rpath)

        fs = filesystem_from_uri(rpath, self.cache_options, storage_options)

        with Context(self.tempdir) as ctx:
            serde.serializer(obj, ctx)
            lpaths = ctx.filenames

        rpaths: str | list[str]
        if len(lpaths) > 1:
            # signals fsspec to put all files into rpath directory
            # TODO: Construct list always to hit the fast path of fs.put()
            rpaths = with_trailing_sep(rpath)
        else:
            rpaths = [rpath]

        fs.put(lpaths, rpaths, **(upload_options or {}))
