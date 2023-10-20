from oneml.processors.dag._client import DagSubmitter
from oneml.processors.ux import (
    CombinedPipeline,
    InPort,
    Inputs,
    NoInputs,
    NoOutputs,
    OutPort,
    Outputs,
    Task,
)
from oneml.services import IExecutable, ServiceId, scoped_service_ids

from ._processors import A, B, C, D


class InB(Inputs):
    x: InPort[float]


class InC(Inputs):
    x: InPort[float]


class InD(Inputs):
    x1: InPort[float]
    x2: InPort[float]


class OutA(Outputs):
    z1: OutPort[float]
    z2: OutPort[float]


class OutB(Outputs):
    z: OutPort[float]


class OutC(Outputs):
    z: OutPort[float]


class DiamondPipeline:
    _dag_submitter: DagSubmitter

    def __init__(self, dag_submitter: DagSubmitter) -> None:
        self._dag_submitter = dag_submitter

    def execute(self) -> None:
        a = Task[NoInputs, OutA](A, "A")
        b = Task[InB, OutB](B, "B")
        c = Task[InC, OutC](C, "C")
        d = Task[InD, NoOutputs](D, "D")

        diamond = CombinedPipeline[NoInputs, NoOutputs](
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
