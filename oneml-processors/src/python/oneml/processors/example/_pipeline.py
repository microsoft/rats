from oneml.processors.dag._client import DagSubmitter
from oneml.processors.ux import PipelineBuilder
from oneml.services import IExecutable, ServiceId, scoped_service_ids

from ._processors import A, B, C, D


class ExamplePipeline:
    _dag_submitter: DagSubmitter

    def __init__(self, dag_submitter: DagSubmitter) -> None:
        self._dag_submitter = dag_submitter

    def execute(self) -> None:
        a = PipelineBuilder.task(A, "A")
        b = PipelineBuilder.task(B, "B")
        c = PipelineBuilder.task(C, "C")
        d = PipelineBuilder.task(D, "D")

        diamond = PipelineBuilder.combine(
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
    PIPELINE = ServiceId[IExecutable]("pipeline")
