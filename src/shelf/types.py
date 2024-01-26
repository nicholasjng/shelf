from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import IO, Any, Callable, Generic, Literal, TypeVar

T = TypeVar("T")


# TODO: Consider splitting these into ReadContext and WriteContext
class Context:
    def __init__(self, tmpdir: str | PathLike[str], filenames: list[str] | None = None):
        self._tmpdir = Path(tmpdir)
        self._fds: deque[IO] = deque()
        self._filenames: list[str] = filenames or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Unwind the file queue by closing
        while self._fds:
            file = self._fds.pop()
            file.close()

    @property
    def files(self):
        return self._fds

    @property
    def filenames(self):
        return self._filenames

    @property
    def tmpdir(self):
        return self._tmpdir

    def directory(self, name: str) -> PathLike[str]:
        return self.tmpdir / name

    def file(self, name: str, **openkwargs: Any) -> IO:
        # TODO: Assert name is not absolute
        fp = self.tmpdir / name
        desc = open(fp, **openkwargs)
        self._fds.append(desc)
        self._filenames.append(str(fp))
        return desc


@dataclass(frozen=True)
class IOPair(Generic[T]):
    serializer: Callable[[T, Context], None]
    deserializer: Callable[[Context], T]


@dataclass(frozen=True)
class CacheOptions:
    directory: PathLike[str]
    type: Literal["blockcache", "filecache", "simplecache"] = "filecache"
