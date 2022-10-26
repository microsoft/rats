from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence

import pydot

from ._pipeline import Pipeline
from ._ux import TaskParam, Workflow


class DotBuilder:
    _g: pydot.Dot = pydot.Dot("DAG", graph_type="digraph")  # type: ignore[no-any-unimported]
    _node_name_mapping: dict[str, str]

    def __init__(self) -> None:
        self._g = pydot.Dot("DAG", graph_type="digraph")
        self._node_name_mapping = {}

    def _format_arguments(self, arguments: Mapping[str, Any], io: Literal["i", "o"]) -> str:
        return "|".join((f"<{io}_{arg}> {arg}" for arg in arguments.keys()))

    def _add_name_to_mapping(self, name: str) -> None:
        if name not in self._node_name_mapping:
            self._node_name_mapping[name] = str(len(self._node_name_mapping))

    def _add_pipeline(self, pipeline: Pipeline) -> None:
        for node in pipeline.nodes:
            name = repr(node)
            self._add_name_to_mapping(name)
            in_arguments = pipeline.nodes[node].sig
            inputs = self._format_arguments(in_arguments, "i")
            out_arguments = pipeline.nodes[node].ret
            outputs = self._format_arguments(out_arguments, "o")

            label = f"{{{{{inputs}}}|{name}|{{{outputs}}}}}"
            node_name = self._node_name_mapping[name]
            self._g.add_node(
                pydot.Node(name=node_name, label=label, shape="Mrecord", color="blue")
            )

        for node, dps in pipeline.dependencies.items():
            name = repr(node)
            for dp in dps:
                dp_name = repr(dp.node)
                out_arg = dp.out_arg.name if dp.node else ""
                if dp_name not in self._node_name_mapping:
                    self._node_name_mapping[dp_name] = str(len(self._node_name_mapping))
                    node_name = self._node_name_mapping[dp_name]
                    label = f"{{{dp_name}}}|{{<o_{out_arg}> {out_arg}}}"
                    self._g.add_node(
                        pydot.Node(name=node_name, label=label, shape="record", color="red")
                    )
                source = self._node_name_mapping[dp_name] + f":o_{out_arg}"
                target = self._node_name_mapping[name] + f":i_{out_arg}"
                self._g.add_edge(pydot.Edge(source, target))

    def _add_inputs(self, inputs: Mapping[str, Sequence[TaskParam]]) -> None:
        name = "inputs"
        self._add_name_to_mapping(name)
        outputs = self._format_arguments(inputs, "o")
        label = f"{{{name}|{{{outputs}}}}}"
        self._g.add_node(
            pydot.Node(
                name=self._node_name_mapping[name], label=label, shape="record", color="red"
            )
        )
        for input, tasks in inputs.items():
            source = self._node_name_mapping[name] + f":o_{input}"
            for task in tasks:
                target = self._node_name_mapping[repr(task.node)] + f":i_{task.param}"
                self._g.add_edge(pydot.Edge(source, target))

    def _add_outputs(self, outputs: Mapping[str, TaskParam]) -> None:
        name = "outputs"
        self._add_name_to_mapping(name)
        inputs = self._format_arguments(outputs, "i")
        label = f"{{{{{inputs}}}|{{{name}}}}}"
        self._g.add_node(
            pydot.Node(
                name=self._node_name_mapping[name], label=label, shape="record", color="red"
            )
        )
        for output, task in outputs.items():
            source = self._node_name_mapping[repr(task.node)] + f":o_{task.param}"
            target = self._node_name_mapping[name] + f":i_{output}"
            self._g.add_edge(pydot.Edge(source, target))

    def add_workflow(self, workflow: Workflow) -> None:
        self._add_pipeline(workflow._pipeline)
        self._add_inputs(workflow._input_targets)
        self._add_outputs(workflow._output_sources)

    def get_dot(self) -> pydot.Dot:  # type: ignore[no-any-unimported]
        return self._g


def dag_to_dot(pipeline: Pipeline) -> pydot.Dot:  # type: ignore[no-any-unimported]
    builder = DotBuilder()
    builder._add_pipeline(pipeline)
    return builder.get_dot()


def workflow_to_dot(workflow: Workflow) -> pydot.Dot:  # type: ignore[no-any-unimported]
    builder = DotBuilder()
    builder.add_workflow(workflow)
    return builder.get_dot()


def dag_to_svg(pipeline: Pipeline) -> bytes:
    dot = dag_to_dot(pipeline)
    return dot.create(format="svg")


def workflow_to_svg(workflow: Workflow) -> bytes:
    dot = workflow_to_dot(workflow)
    return dot.create(format="svg")
