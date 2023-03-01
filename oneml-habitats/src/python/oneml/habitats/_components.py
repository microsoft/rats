from typing import Any, NamedTuple

from immunodata.cli import ILocateDiContainers

from oneml.habitats._publishers import NodeBasedPublisher, SinglePortPublisher
from oneml.pipelines.session._components import ComponentId


class _Components(NamedTuple):
    DI_LOCATOR: ComponentId[ILocateDiContainers]
    NODE_PUBLISHER: ComponentId[NodeBasedPublisher]
    SINGLE_PORT_PUBLISHER: ComponentId[SinglePortPublisher[Any]]


OnemlHabitatsComponents = _Components(
    DI_LOCATOR=ComponentId("oneml-habitats:di-locator"),
    NODE_PUBLISHER=ComponentId("oneml-habitats:node-publisher"),
    SINGLE_PORT_PUBLISHER=ComponentId("oneml-habitats:single-port-publisher"),
)
