# type: ignore
# flake8: noqa
"""Classes for object identifiers.

We use strings to identify objects such as DAG nodes and ports of those nodes.

Classes in this module extend the standard python string to support:

1. Static typing of the role of an identifier, e.g. that a node idetifier is not used as a port identifier.
1. The identifiers only include allowed characters.
"""


from __future__ import annotations

from abc import abstractclassmethod
from typing import Generic, Optional, Tuple, Type, TypeVar, overload

_level_separator = "/"
"""Separator between levels of a multi-level identifier, e.g. the identifier of a node in a flattened DAG."""

_member_separator = "."
"""Separator between an identifier of an object (e.g. a node) and an identifier of a member of the object (e.g. a port)."""


IdentifierT = TypeVar("IdentifierT")


class Identifier(str):
    """Identifier."""

    __slots__ = ()

    def __new__(cls, identifier: str) -> Identifier:
        return super().__new__(cls, identifier)

    def __add__(self, other: IdentifierT) -> IdentifierT:
        return other.__class__(f"{self}{_level_separator}{other}")


class ObjectIdentifier(Identifier):
    f"""Object identifier.  Cannot include the member separator `{_member_separator}`."""
    __slots__ = ()

    def __new__(cls, identifier: str) -> ObjectIdentifier:
        if _member_separator in identifier:
            raise ValueError(f"Cannot include <{_member_separator}> in <{cls}>.")
        return super().__new__(cls, identifier)


class SimpleObjectIdentifier(ObjectIdentifier):
    f"""Single level identifier.  Cannot include the member separator `{_member_separator}` or the nesting separator `{_level_separator}`."""
    __slots__ = ()

    def __new__(cls, identifier: str) -> SimpleObjectIdentifier:
        if _level_separator in identifier:
            raise ValueError(f"Cannot include <{_level_separator}> in <{cls}>.")
        return super().__new__(cls, identifier)


ObjectIdentifierT = TypeVar("ObjectIdentifierT", bound=ObjectIdentifier)
MemberIdentifierT = TypeVar("MemberIdentifierT", bound=ObjectIdentifier)


class Address(Identifier, Generic[ObjectIdentifierT, MemberIdentifierT]):
    f"""Identifies a member of an object from outside the object.  E.g. Node{_member_separator}Port."""
    __slots__ = ("_object_name", "_member_name")

    @overload
    def __new__(cls, address: str) -> Address[ObjectIdentifierT, MemberIdentifierT]:
        ...

    @overload
    def __new__(
        cls, member_name: str, object_name: str
    ) -> Address[ObjectIdentifierT, MemberIdentifierT]:
        ...

    def __new__(
        cls: Type[Address[ObjectIdentifierT, MemberIdentifierT]],
        first: str,
        second: Optional[str] = None,
    ) -> Address[ObjectIdentifierT, MemberIdentifierT]:
        # This method allows creating an Address object by passing in either
        # * a single parameter holding the address in Object.Member format
        # * two parameters - object, and member
        # The two @overload definitions generate a docstring describing these two options with the
        # correct parameter names.  The parameter names specified here do not make it to the docstring.
        if second is not None:
            address = f"{first}{_member_separator}{second}"
            object_name = first
            member_name = second
        else:
            address = first
            object_name, member_name = first.split(_member_separator)

        object_class = cls._get_object_class()
        member_class = cls._get_member_class()
        self = super().__new__(cls, address)
        self._object_name = object_class(object_name)
        self._member_name = member_class(member_name)
        return self

    def __iter__(self) -> Tuple[ObjectIdentifierT, MemberIdentifierT]:
        return (self._object_name, self._member_name).__iter__()

    @abstractclassmethod
    def _get_object_class(cls) -> Type[ObjectIdentifier]:
        ...

    @abstractclassmethod
    def _get_member_class(cls) -> Type[ObjectIdentifier]:
        ...
