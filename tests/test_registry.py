import pytest

import shelf
from shelf.registry import lookup, registry


def test_registration() -> None:
    """Type registration tests."""
    shelf.register_type(tuple, lambda t: "my-tuple.txt", lambda fp: tuple())

    assert tuple in registry

    with pytest.raises(RuntimeError, match="type .* already registered"):
        shelf.register_type(tuple, lambda t: "my-type.txt", lambda fp: tuple())

    def new_ser(t: tuple) -> str:
        return "my-tuple.json"

    def new_deser(fp: str) -> tuple:
        return ("hello",)

    shelf.register_type(tuple, new_ser, new_deser, clobber=True)

    io = lookup(tuple)
    assert io.serializer == new_ser
    assert io.deserializer == new_deser


def test_deregistration() -> None:
    class MyType:
        pass

    shelf.register_type(MyType, lambda t: "my-type.txt", lambda fp: MyType())
    assert MyType in registry
    shelf.deregister_type(MyType)
    assert MyType not in registry
