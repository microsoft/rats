from dataclasses import dataclass
from typing import Generic, NamedTuple, TypeVar

T_GroupType = TypeVar("T_GroupType", bound=NamedTuple)


@dataclass(frozen=True)
class GroupAnnotations(Generic[T_GroupType]):
    """The list of T_GroupType objects identified by a given name in a namespace."""

    name: str
    """The name of the annotation, typically the name of the function in a class"""
    namespace: str
    """All the groups in a namespace are expected to be of the same T_GroupType."""
    groups: tuple[T_GroupType, ...]
