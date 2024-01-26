import pytest

import shelf
from shelf.registry import lookup, registry


def test_registration() -> None:
    """Type registration tests."""
    shelf.register_type(tuple, lambda t, ctx: None, lambda fp: tuple())

    assert tuple in registry

    with pytest.raises(RuntimeError, match="type .* already registered"):
        shelf.register_type(tuple, lambda t, ctx: None, lambda fp: tuple())

    def new_ser(t: tuple, ctx: shelf.Context) -> None:
        pass

    def new_deser(ctx: shelf.Context) -> tuple:
        return ("hello",)

    shelf.register_type(tuple, new_ser, new_deser, clobber=True)

    io = lookup(tuple)
    assert io.serializer == new_ser
    assert io.deserializer == new_deser


def test_deregistration() -> None:
    class MyType:
        pass

    shelf.register_type(MyType, lambda t, ctx: None, lambda fp: MyType())
    assert MyType in registry
    shelf.deregister_type(MyType)
    assert MyType not in registry
