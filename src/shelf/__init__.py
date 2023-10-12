from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("shelf")
except PackageNotFoundError:
    # package is not installed
    pass


from .registry import deregister_type, get_hooks, register_type
