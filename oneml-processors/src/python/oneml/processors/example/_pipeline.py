from oneml.processors.dag._client import DagSubmitter
from oneml.processors.ux import (
    CombinedPipeline,
    InEntry,
    Inputs,
    NoInCollections,
    NoInputs,
    NoOutCollections,
    NoOutputs,
    OutEntry,
    Outputs,
    Task,
)
from oneml.services import IExecutable, ServiceId, scoped_service_ids

from ._processors import A, B, C, D


class InB(Inputs):
    x: InEntry[float]


class InC(Inputs):
    x: InEntry[float]


class InD(Inputs):
    x1: InEntry[float]
    x2: InEntry[float]


class OutA(Outputs):
    z1: OutEntry[float]
    z2: OutEntry[float]


class OutB(Outputs):
    z: OutEntry[float]


class OutC(Outputs):
    z: OutEntry[float]


class DiamondPipeline:
    _dag_submitter: DagSubmitter

    def __init__(self, dag_submitter: DagSubmitter) -> None:
        self._dag_submitter = dag_submitter

    def execute(self) -> None:
        a = Task[NoInputs, OutA](A, "A")
        b = Task[InB, OutB](B, "B")
        c = Task[InC, OutC](C, "C")
        d = Task[InD, NoOutputs](D, "D")

        diamond = CombinedPipeline[NoInputs, NoOutputs, NoInCollections, NoOutCollections](
            pipelines=[a, b, c, d],
            dependencies=(
                b.inputs.x << a.outputs.z1,
                c.inputs.x << a.outputs.z2,
                d.inputs.x1 << b.outputs.z,
                d.inputs.x2 << c.outputs.z,
            ),
            name="diamond",
        )

        self._dag_submitter.submit_dag(diamond._dag)


@scoped_service_ids
class DiamondExampleServices:
    DIAMOND = ServiceId[IExecutable]("diamond")
