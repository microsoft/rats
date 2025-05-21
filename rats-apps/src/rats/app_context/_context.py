from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, final

import dataclass_wizard

from rats import apps

logger = logging.getLogger(__name__)
T_ContextType = TypeVar("T_ContextType")  # TODO: figure out how to bind this to dataclasses :(
"""
Generic type for context value objects.

!!! warning
    Python lacks the ability to bind generic values to require them to be a
    [dataclasses.dataclass][] instance, but all [rats.app_context.T_ContextType][] instances must
    be dataclasses in order for them to serialize and deserialize. This is mostly a leaky private
    detail, and we hope to remove this requirement in the future.
"""
ContextValue = dict[str, Any]
"""Values found in [rats.app_context.Context][] in their simple value type representations."""


@final
@dataclass(frozen=True)
class Context(dataclass_wizard.JSONSerializable, Generic[T_ContextType]):
    """
    An easily serializable class to hold one or more values tied to a service id.

    We can use these instances to share simple value types across a cluster of machines, and
    integrate them with [rats.apps.Container][] to make the business logic unaware of any
    complexity in here.
    """

    service_id: apps.ServiceId[T_ContextType]
    """
    The [rats.apps.ServiceId][] the remote app will be able to use to retrieve the stored values.
    """
    values: tuple[ContextValue, ...]
    """The encoded value object, ready to be turned into json for marshaling."""

    @staticmethod
    def make(
        service_id: apps.ServiceId[T_ContextType],
        *contexts: T_ContextType,
    ) -> Context[T_ContextType]:
        """
        Convert a dataclass into a context object tied to the provided service id.

        ```python
        from dataclass import dataclass


        @dataclass(frozen=True)
        class MySimpleData:
            blob_path: Tuple[str, str, str]
            offset: int


        service_id = apps.ServiceId[MySimpleData]("example-service")
        ctx = app_context.Context[MySimpleData].make(
            service_id,
            MySimpleData(
                blob_path=("accountname", "containername", "/some/blob/path"),
            ),
        )
        ```

        Args:
            service_id: The service id the context values will be retrievable as.
            *contexts: Zero or more [rats.app_context.T_ContextType][] instances.
        """
        if len(contexts) > 0:
            cls = contexts[0].__class__
            dataclass_wizard.DumpMeta(key_transform="NONE").bind_to(cls)  # type: ignore[reportUnknownMemberType]
        return Context(
            service_id,
            tuple([dataclass_wizard.asdict(ctx) for ctx in contexts]),  # type: ignore
        )
