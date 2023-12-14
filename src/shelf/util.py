from fsspec.utils import get_protocol, stringify_path


def is_fully_qualified(path: str) -> bool:
    path = stringify_path(path)
    protocol = get_protocol(path)
    return any(path.startswith(protocol + sep) for sep in ("::", "://"))
