from typing import NamedTuple

from oneml.pipelines.session import IOManagerRegistry, ServiceId


class _Services(NamedTuple):
    GetActiveNodeKey: ServiceId[str]
    IOManagerRegistry: ServiceId[IOManagerRegistry]
    SessionId: ServiceId[str]


OnemlProcessorServices = _Services(
    GetActiveNodeKey=ServiceId("oneml-processor:get-active-node-key"),
    IOManagerRegistry=ServiceId("oneml-processors:iomanager-registry"),
    SessionId=ServiceId("oneml-processors:session-id"),
)
