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
    """Register serialization/deserialization hooks for a given type t."""
    if t in _registry and not clobber:
        raise RuntimeError(f"type {t} is already registered, rerun with clobber=True to override")

    _registry[t] = IO(serializer, deserializer)


def deregister_type(t: type) -> None:
    """Remove a type's serialize/deserialize hooks from the type registry."""
    _registry.pop(t, None)


def get_hooks(t: type, strict: bool = False, bound: type | None = None) -> IO:
    """
    Returns a type's registered serialization/deserialization hooks.

    Parameters
    ----------
    t: The Python type to return registered hooks for.
    strict: Whether to allow returning a supertype's registered hooks if any are found.
    bound: A type bound (inclusive) at which to stop walking up the requested type's method resolution order (MRO) when allowing supertype matches (i.e., when strict=False).

    Returns
    -------
    A tuple of registered ser/de hooks.

    Raises
    ------
    KeyError: If the requested type (or all of its eligible supertypes) has no ser/de hooks available.
    """

    if hasattr(t, "__mro__") and not strict:
        # we exclude object as a type explicitly.
        type_order = t.__mro__[:-1]
    else:
        type_order = (t,)

    for typ in type_order:
        try:
            return _registry[typ]
        except KeyError:
            pass

        if type == bound:
            break

    msg = f"no ser/de hooks registered for type {t}"
    if not strict:
        msg += f" or any suitable supertype (considered: {type_order})"

    raise KeyError(msg)