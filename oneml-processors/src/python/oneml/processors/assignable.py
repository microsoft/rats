from __future__ import annotations

import copy
from collections import defaultdict
from typing import Any, Dict, TypeVar, Union

from .identifiers import _member_separator

T = TypeVar("T")


class Assignable:
    """Base class for immutable types with .assign that returns a shallow copy with modifiactions."""

    def assign(self: T, **kwargs: Union[Any, Dict[str, Any]]) -> T:
        f"""Get a copy of self with modified attributes.

        Args:
            kwargs: A mapping from attribute to new value.  Nested attributes can be specified
                using <{_member_separator}> to seperate levels.  Does not support assigning to
                attributes that do not already exist.
        """
        result = copy.copy(self)

        def assign_attribute(k: str, v: Any) -> None:
            if not hasattr(result, k):
                raise AttributeError(f"Cannot assign to non-existing attribute <{k}>.")
            setattr(result, k, v)

        prefixes: Dict[str, Any] = defaultdict(dict)
        for k, v in kwargs.items():
            if _member_separator in k:
                k, kn = k.split(_member_separator, 1)
                prefixes[k][kn] = v
            else:
                assign_attribute(k, v)
        for k, sub in prefixes.items():
            v = getattr(result, k).assign(**sub)
            assign_attribute(k, v)
        return result
