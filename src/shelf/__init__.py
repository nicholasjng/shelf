from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("shelf")
except PackageNotFoundError:
    # package is not installed
    pass


from .core import Shelf
from .registry import deregister_type, lookup, register_type
