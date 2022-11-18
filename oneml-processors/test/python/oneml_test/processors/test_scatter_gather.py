from typing import Any, Dict, TypedDict

from oneml.processors import (
    InputDataProcessor,
    OutProcessorParam,
    Pipeline,
    PipelineBuilder,
    PipelineRunner,
    ScatterGatherBuilders,
    frozendict,
)


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> Dict[str, OutProcessorParam]:
        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
        return {out_name: OutProcessorParam(out_name, str) for out_name in out_names}

    def process(self, in1: str, in2: str) -> Dict[str, Any]:
        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
        }


def get_scatter_pipeline(K: int) -> Pipeline:
    return PipelineBuilder.task(
        "scatter",
        Scatter,
        params_getter=frozendict(K=K),
        return_annotation=Scatter.get_return_annotation(K),
    )


BatchProcessOutput = TypedDict("BatchProcessOutput", {"out12": str, "out23": str})


class BatchProcess:
    def process(self, in1: str, in2: str, in3: str) -> BatchProcessOutput:
        return BatchProcessOutput(out12=in1 + "*" + in2, out23=in2 + "*" + in3)


def get_batch_process_pipeline() -> Pipeline:
    return PipelineBuilder.task("batch_process", BatchProcess)


ConcatStringsAsLinesOutput = TypedDict("ConcatStringsAsLinesOutput", {"out": str})


class ConcatStringsAsLines:
    def process(self, *inp: str) -> ConcatStringsAsLinesOutput:
        return ConcatStringsAsLinesOutput(out="\n".join(inp))


def get_concat_strings_as_lines_pipeline(port_name: str) -> Pipeline:
    w = PipelineBuilder.task(f"concat_{port_name}", ConcatStringsAsLines)
    w = PipelineBuilder.combine(
        w, name=w.name, inputs={port_name: w.inputs.inp}, outputs={port_name: w.outputs.out}
    )
    return w


def get_gather_pipeline() -> Pipeline:
    return PipelineBuilder.combine(
        get_concat_strings_as_lines_pipeline("out12"),
        get_concat_strings_as_lines_pipeline("out23"),
        name="gather",
    )


def get_data_pipeline() -> Pipeline:
    in1 = PipelineBuilder.task(
        "in1",
        InputDataProcessor,
        params_getter=frozendict(data={"in1": "IN1"}),
        return_annotation=InputDataProcessor.get_return_annotation(in1="IN1"),
    )
    in2 = PipelineBuilder.task(
        "in2",
        InputDataProcessor,
        params_getter=frozendict(data={"in2": "IN2"}),
        return_annotation=InputDataProcessor.get_return_annotation(in2="IN2"),
    )
    in3 = PipelineBuilder.task(
        "in3",
        InputDataProcessor,
        params_getter=frozendict(data={"in3": "IN3"}),
        return_annotation=InputDataProcessor.get_return_annotation(in3="IN3"),
    )
    return PipelineBuilder.combine(in1, in2, in3, name="pl")


def test_scatter_gather() -> None:
    scatter = get_scatter_pipeline(4)
    batch_process = get_batch_process_pipeline()
    gather = get_gather_pipeline()
    sc = ScatterGatherBuilders.build("sc", scatter, batch_process, gather)
    data_pl = get_data_pipeline()
    test_sc = PipelineBuilder.combine(
        sc,
        data_pl,
        name="test_sc",
        dependencies=(
            sc.inputs.in1 << data_pl.outputs.in1,
            sc.inputs.in2 << data_pl.outputs.in2,
            sc.inputs.in3 << data_pl.outputs.in3,
        ),
    )
    runner = PipelineRunner(test_sc)
    o = runner()
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


def get_gather_pipeline_with_numbered_inputs(K: int) -> Pipeline:
    w12 = get_concat_strings_as_lines_pipeline("out12")
    w23 = get_concat_strings_as_lines_pipeline("out23")
    return PipelineBuilder.combine(
        w12,
        w23,
        name="gather",
        dependencies=(),
        inputs=(
            {f"out12.{k}": w12.inputs.out12.concat_out12 for k in range(K)}
            | {f"out23.{k}": w23.inputs.out23.concat_out23 for k in range(K)}
        ),
    )


def test_scatter_gather_with_numbered_gather_inputs() -> None:
    scatter = get_scatter_pipeline(4)
    batch_process = get_batch_process_pipeline()
    gather = get_gather_pipeline_with_numbered_inputs(4)
    sc = ScatterGatherBuilders.build("sc", scatter, batch_process, gather)
    data_pl = get_data_pipeline()
    test_sc = PipelineBuilder.combine(
        sc,
        data_pl,
        name="test_sc",
        dependencies=(
            sc.inputs.in1 << data_pl.outputs.in1,
            sc.inputs.in2 << data_pl.outputs.in2,
            sc.inputs.in3 << data_pl.outputs.in3,
        ),
    )
    runner = PipelineRunner(test_sc)
    o = runner()
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
