from typing import Any, TypedDict

from rats.processors._legacy_subpackages.training import ScatterGatherBuilders
from rats.processors._legacy_subpackages.utils import frozendict
from rats.processors._legacy_subpackages.ux import (
    PipelineRunnerFactory,
    UPipeline,
    UPipelineBuilder,
)


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> dict[str, type]:
        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
        return {out_name: str for out_name in out_names}

    @classmethod
    def get_renames(cls, K: int) -> dict[str, str]:
        return {f"in1_{k}": f"in1.{k}" for k in range(K)} | {
            f"in2_{k}": f"in2.{k}" for k in range(K)
        }

    def process(self, in1: str, in2: str) -> dict[str, Any]:
        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
        }


def get_scatter_pipeline(K: int) -> UPipeline:
    return UPipelineBuilder.task(
        Scatter,
        "scatter",
        config=frozendict(K=K),
        return_annotation=Scatter.get_return_annotation(K),
    ).rename_outputs(Scatter.get_renames(K))


class BatchProcessOutput(TypedDict):
    out12: str
    out23: str


class BatchProcess:
    def process(self, in1: str, in2: str, in3: str) -> BatchProcessOutput:
        return BatchProcessOutput(out12=in1 + "*" + in2, out23=in2 + "*" + in3)


def get_batch_process_pipeline() -> UPipeline:
    return UPipelineBuilder.task(BatchProcess, "batch_process")


class ConcatStringsAsLinesOutput(TypedDict):
    out: str


class ConcatStringsAsLines:
    def process(self, **inp: str) -> ConcatStringsAsLinesOutput:
        return ConcatStringsAsLinesOutput(out="\n".join(inp.values()))


def get_concat_strings_as_lines_pipeline(port_name: str, K: int) -> UPipeline:
    w = (
        UPipelineBuilder.task(
            ConcatStringsAsLines,
            f"concat_{port_name}",
            input_annotation={f"{port_name}_{k}": str for k in range(K)},
        )
        .rename_inputs({f"{port_name}_{k}": f"{port_name}.{k}" for k in range(K)})
        .rename_outputs({"out": port_name})
    )
    return w


def get_gather_pipeline(K: int) -> UPipeline:
    return UPipelineBuilder.combine(
        pipelines=[
            get_concat_strings_as_lines_pipeline("out12", K),
            get_concat_strings_as_lines_pipeline("out23", K),
        ],
        name="gather",
    )


def test_scatter_gather(pipeline_runner_factory: PipelineRunnerFactory) -> None:
    scatter = get_scatter_pipeline(4)
    batch_process = get_batch_process_pipeline()
    gather = get_gather_pipeline(4)
    sc = ScatterGatherBuilders.build("sc", scatter, batch_process, gather)
    runner = pipeline_runner_factory(sc)
    o = runner(dict(in1="IN1", in2="IN2", in3="IN3"))
    expected_out12 = "\n".join(
        (
            "IN1_0*IN2_0",
            "IN1_1*IN2_1",
            "IN1_2*IN2_2",
            "IN1_3*IN2_3",
        )
    )
    expected_out23 = "\n".join(
        (
            "IN2_0*IN3",
            "IN2_1*IN3",
            "IN2_2*IN3",
            "IN2_3*IN3",
        )
    )
    assert set(o) == set(("out12", "out23"))
    assert o.out12 == expected_out12
    assert o.out23 == expected_out23
