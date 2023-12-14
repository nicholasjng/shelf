import pytest

from shelf.util import is_fully_qualified


@pytest.mark.parametrize(
    "path,expected",
    [
        ("file:///hello.txt", True),
        ("hello.txt", False),
        ("s3://hello.txt", True),
        ("filecache::s3//hello.txt", True),
    ],
)
def test_fully_qualified_paths(path: str, expected: bool) -> None:
    actual = is_fully_qualified(path)
    assert actual == expected
