import types
from typing import Callable, NamedTuple


class IO(NamedTuple):
    serializer: Callable
    deserializer: Callable

# internal, mutable
_registry: dict[type, IO] = {}

# external, immutable
registry = types.MappingProxyType(_registry)


def register_type(
    t: type, serializer: Callable, deserializer: Callable, clobber: bool = False
) -> None:
    """Register serializer and deserializer for a given type t."""
    if t in _registry and not clobber:
        raise RuntimeError(f"type {t} is already registered, rerun with clobber=True to override")

    _registry[t] = IO(serializer, deserializer)


def deregister_type(t: type) -> None:
    """Remove a type's serializer and deserializer from the type registry."""
    _registry.pop(t, None)


def lookup(t: type, strict: bool = True, bound: type | None = None) -> IO:
    """
    Returns a type's registered serialization/deserialization functions.

    Parameters
    ----------
    t: A Python type for which to return the registered IO.
    strict: Only allow exact type matches instead of any supertype's registered IO if found.
    bound: An inclusive type bound at which to stop walking up the requested type's
    method resolution order (MRO) when allowing supertype matches (i.e., when `strict=False`).

    Returns
    -------
    A registered serializer/deserializer tuple.

    Raises
    ------
    KeyError: If the requested type (and all of its eligible supertypes) has no ser/de available.
    """

    if hasattr(t, "__mro__") and not strict:
        type_order = t.__mro__
    else:
        type_order = (t,)

    n = len(type_order)
    for typ in type_order:
        try:
            return _registry[typ]
        except KeyError:
            pass

        if typ == bound:
            # `bound` is inclusive
            n = type_order.index(bound) + 1
            break

    msg = f"no IO registered for type {t}"
    if not strict:
        msg += f" or any suitable supertype (considered {type_order[:n]})"

    raise KeyError(msg)
