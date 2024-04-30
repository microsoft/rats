from typing import Generic, NamedTuple, TypeVar

T_GroupType = TypeVar("T_GroupType", bound=NamedTuple)


class GroupAnnotations(NamedTuple, Generic[T_GroupType]):
    """The list of service ids attached to a given function."""

    name: str
    """The name of the function."""
    namespace: str
    """All the groups in a namespace are expected to be of the same T_GroupType."""
    groups: tuple[T_GroupType, ...]
