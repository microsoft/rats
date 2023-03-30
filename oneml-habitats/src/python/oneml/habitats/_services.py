from typing import Any, NamedTuple

from immunodata.cli import ILocateDiContainers

from oneml.habitats._publishers import NodeBasedPublisher, SinglePortPublisher
from oneml.pipelines.session import ServiceId


class _Services(NamedTuple):
    DI_LOCATOR: ServiceId[ILocateDiContainers]
    NODE_PUBLISHER: ServiceId[NodeBasedPublisher]
    SINGLE_PORT_PUBLISHER: ServiceId[SinglePortPublisher[Any]]


OnemlHabitatsServices = _Services(
    DI_LOCATOR=ServiceId("oneml-habitats:di-locator"),
    NODE_PUBLISHER=ServiceId("oneml-habitats:node-publisher"),
    SINGLE_PORT_PUBLISHER=ServiceId("oneml-habitats:single-port-publisher"),
)
