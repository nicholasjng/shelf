import os

from fsspec.utils import get_protocol, stringify_path


def is_fully_qualified(path: str) -> bool:
    path = stringify_path(path)
    protocol = get_protocol(path)
    return any(path.startswith(protocol + sep) for sep in ("::", "://"))


def with_trailing_sep(path: str) -> str:
    return path if path.endswith(os.sep) else path + os.sep
