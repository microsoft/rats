from typing import Any, Dict, TypedDict

from oneml.processors import (
    InputDataProcessor,
    OutParameter,
    ScatterGatherBuilders,
    Workflow,
    WorkflowClient,
    WorkflowRunner,
    frozendict,
)


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> Dict[str, OutParameter]:
        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
        return {out_name: OutParameter(out_name, str) for out_name in out_names}

    def process(self, in1: str, in2: str) -> Dict[str, Any]:
        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
        }


def get_scatter_workflow(K: int) -> Workflow:
    return WorkflowClient.task(
        "scatter", Scatter, frozendict(K=K), return_annotation=Scatter.get_return_annotation(K)
    )


BatchProcessOutput = TypedDict("BatchProcessOutput", {"out12": str, "out23": str})


class BatchProcess:
    def process(self, in1: str, in2: str, in3: str) -> BatchProcessOutput:
        return BatchProcessOutput(out12=in1 + "*" + in2, out23=in2 + "*" + in3)


def get_batch_process_workflow() -> Workflow:
    return WorkflowClient.task("batch_process", BatchProcess)


ConcatStringsAsLinesOutput = TypedDict("ConcatStringsAsLinesOutput", {"out": str})


class ConcatStringsAsLines:
    def process(self, *inp: str) -> ConcatStringsAsLinesOutput:
        return ConcatStringsAsLinesOutput(out="\n".join(inp))


def get_concat_strings_as_lines_workflow(port_name: str) -> Workflow:
    w = WorkflowClient.task(f"concat_{port_name}", ConcatStringsAsLines)
    w = WorkflowClient.combine(
        w, name=w.name, inputs={port_name: w.inputs.inp}, outputs={port_name: w.outputs.out}
    )
    return w


def get_gather_workflow() -> Workflow:
    return WorkflowClient.combine(
        get_concat_strings_as_lines_workflow("out12"),
        get_concat_strings_as_lines_workflow("out23"),
        name="gather",
    )


def get_data_workflow() -> Workflow:
    in1 = WorkflowClient.task(
        "in1",
        InputDataProcessor,
        params_getter=frozendict(data={"in1": "IN1"}),
        return_annotation=InputDataProcessor.get_return_annotation(in1="IN1"),
    )
    in2 = WorkflowClient.task(
        "in2",
        InputDataProcessor,
        params_getter=frozendict(data={"in2": "IN2"}),
        return_annotation=InputDataProcessor.get_return_annotation(in2="IN2"),
    )
    in3 = WorkflowClient.task(
        "in3",
        InputDataProcessor,
        params_getter=frozendict(data={"in3": "IN3"}),
        return_annotation=InputDataProcessor.get_return_annotation(in3="IN3"),
    )
    return WorkflowClient.combine(in1, in2, in3, name="wf")


def test_scatter_gather() -> None:
    scatter = get_scatter_workflow(4)
    batch_process = get_batch_process_workflow()
    gather = get_gather_workflow()
    sc = ScatterGatherBuilders.build("sc", scatter, batch_process, gather)
    data_wf = get_data_workflow()
    test_sc = WorkflowClient.combine(
        sc,
        data_wf,
        name="test_sc",
        dependencies=(
            sc.inputs.in1 << data_wf.outputs.in1,
            sc.inputs.in2 << data_wf.outputs.in2,
            sc.inputs.in3 << data_wf.outputs.in3,
        ),
    )
    runner = WorkflowRunner(test_sc)
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


def get_gather_workflow_with_numbered_inputs(K: int) -> Workflow:
    w12 = get_concat_strings_as_lines_workflow("out12")
    w23 = get_concat_strings_as_lines_workflow("out23")
    return WorkflowClient.combine(
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
    scatter = get_scatter_workflow(4)
    batch_process = get_batch_process_workflow()
    gather = get_gather_workflow_with_numbered_inputs(4)
    sc = ScatterGatherBuilders.build("sc", scatter, batch_process, gather)
    data_wf = get_data_workflow()
    test_sc = WorkflowClient.combine(
        sc,
        data_wf,
        name="test_sc",
        dependencies=(
            sc.inputs.in1 << data_wf.outputs.in1,
            sc.inputs.in2 << data_wf.outputs.in2,
            sc.inputs.in3 << data_wf.outputs.in3,
        ),
    )
    runner = WorkflowRunner(test_sc)
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
