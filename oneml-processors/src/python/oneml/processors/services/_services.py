from typing import NamedTuple

from oneml.pipelines.session import ServiceId


class _Services(NamedTuple):
    GetActiveNodeKey: ServiceId[str]


OnemlProcessorServices = _Services(
    GetActiveNodeKey=ServiceId("oneml-processor:get-active-node-key")
)
