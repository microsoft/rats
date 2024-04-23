from rats.processors._legacy_subpackages.dag._client import DagSubmitter
from rats.processors._legacy_subpackages.registry import IProvidePipeline
from rats.processors._legacy_subpackages.ux import (
    CombinedPipeline,
    InPort,
    Inputs,
    NoInputs,
    OutPort,
    Outputs,
    Pipeline,
    Task,
)

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


class OutD(Outputs):
    z1: OutPort[float]
    z2: OutPort[float]


DiamondPipeline = Pipeline[NoInputs, OutD]


class DiamondPipelineProvider(IProvidePipeline[DiamondPipeline]):
    def __call__(self) -> DiamondPipeline:
        a = Task[NoInputs, OutA](A, "A")
        b = Task[InB, OutB](B, "B")
        c = Task[InC, OutC](C, "C")
        d = Task[InD, OutD](D, "D")

        return CombinedPipeline(
            pipelines=[a, b, c, d],
            dependencies=(
                b.inputs.x << a.outputs.z1,
                c.inputs.x << a.outputs.z2,
                d.inputs.x1 << b.outputs.z,
                d.inputs.x2 << c.outputs.z,
            ),
            name="diamond",
        )


class DiamondExecutable:
    _dag_submitter: DagSubmitter
    _diamond_provider: IProvidePipeline[DiamondPipeline]

    def __init__(
        self, dag_submitter: DagSubmitter, diamond_provider: IProvidePipeline[DiamondPipeline]
    ) -> None:
        self._dag_submitter = dag_submitter
        self._diamond_provider = diamond_provider

    def execute(self) -> None:
        self._dag_submitter.submit_dag(self._diamond_provider()._dag)
