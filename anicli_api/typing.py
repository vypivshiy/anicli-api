import sys


if sys.version_info >= (3, 11):
    # (used in rest-API clients as Result monad container)
    # Changed in version 3.11: Added support for generic namedtuples.
    from typing import NamedTuple

    # (used in rest-API clients as annotating json responses)
    # Changed in version 3.11: Added support for marking individual keys as Required or NotRequired. See PEP 655.
    # Changed in version 3.11: Added support for generic TypedDicts.
    from typing import TypedDict, Required, NotRequired
else:
    from typing_extensions import NamedTuple, TypedDict, Required, NotRequired


if sys.version_info >= (3, 8):
    from collections.abc import Sequence, MutableSequence, Awaitable
else:
    from typing import Sequence, MutableSequence, Awaitable

__all__ = ["NamedTuple", "TypedDict", "Required", "NotRequired", "Sequence", "MutableSequence", "Awaitable"]
