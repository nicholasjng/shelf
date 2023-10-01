from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("museum")
except PackageNotFoundError:
    # package is not installed
    pass
