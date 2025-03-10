from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, final

import dataclass_wizard

from rats import apps

logger = logging.getLogger(__name__)
T_ContextType = TypeVar("T_ContextType")  # TODO: figure out how to bind this to dataclasses :(
ContextValue = dict[str, Any]


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
    values: tuple[ContextValue, ...]

    @staticmethod
    def make(
        service_id: apps.ServiceId[T_ContextType],
        *contexts: T_ContextType,
    ) -> Context[T_ContextType]:
        """
        Convert a dataclass into a context object tied to the provided service id.

        ```python
        from dataclass import dataclass


        class MySimpleData:
            blob_path: Tuple[str, str, str]
            offset: int


        ctx = app_context.Context[MySimpleData].make(
            MySimpleData(
                blob_path=("accountname", "containername", "/some/blob/path"),
            )
        )
        ```
        """
        return Context(
            service_id,
            tuple([dataclass_wizard.asdict(ctx) for ctx in contexts]),  # type: ignore
        )
