from __future__ import annotations

import os
from typing import Any

from fsspec import AbstractFileSystem, filesystem
from fsspec.utils import get_protocol, stringify_path

from shelf.types import CacheOptions


def filesystem_from_uri(
    uri: str,
    cache_options: CacheOptions | None = None,
    storage_options: dict[str, Any] | None = None,
) -> AbstractFileSystem:
    protocol = get_protocol(uri)
    storage_options = storage_options or {}
    if cache_options is not None:
        protocol = cache_options.type
        kwargs = {
            "target_protocol": cache_options.type,
            "target_options": storage_options,
            "cache_storage": cache_options.directory,
        }
    else:
        kwargs = storage_options

    fs: AbstractFileSystem = filesystem(protocol, **kwargs)
    return fs


def is_fully_qualified(path: str | os.PathLike[str]) -> bool:
    path = stringify_path(path)
    protocol = get_protocol(path)
    return any(path.startswith(protocol + sep) for sep in ("::", "://"))


def with_trailing_sep(path: str | os.PathLike[str]) -> str:
    path = stringify_path(path)
    return path if path.endswith(os.sep) else path + os.sep
