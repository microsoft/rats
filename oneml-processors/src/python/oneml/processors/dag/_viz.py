from __future__ import annotations

from typing import Any, Iterable, Literal, Mapping

import pydot

from ..ux._pipeline import InParameter, OutParameter, Pipeline
from ._dag import DAG


class DotBuilder:
    _g: pydot.Dot  # type: ignore[no-any-unimported]
    _node_name_mapping: dict[str, str]

    def __init__(self) -> None:
        self._g = pydot.Dot("DAG", graph_type="digraph")
        self._node_name_mapping = {}

    def _format_arguments(self, arguments: Iterable[str], io: Literal["i", "o"]) -> str:
        return "|".join((f"<{io}_{arg}> {arg}" for arg in arguments))

    def _add_name_to_mapping(self, name: str) -> None:
        if name not in self._node_name_mapping:
            self._node_name_mapping[name] = str(len(self._node_name_mapping))

    def _add_pipeline(self, dag: DAG) -> None:
        for node in dag.nodes:
            name = repr(node)
            self._add_name_to_mapping(name)
            in_arguments = tuple(k.name for k in dag.nodes[node].inputs.values())
            inputs = self._format_arguments(in_arguments, "i")
            out_arguments = tuple(k.name for k in dag.nodes[node].outputs.values())
            outputs = self._format_arguments(out_arguments, "o")

            label = f"{{{{{inputs}}}|{name}|{{{outputs}}}}}"
            node_name = self._node_name_mapping[name]
            self._g.add_node(
                pydot.Node(name=node_name, label=label, shape="Mrecord", color="blue")
            )

        for node, dps in dag.dependencies.items():
            name = repr(node)
            for dp in dps:
                dp_name = repr(dp.node)
                in_arg = dp.in_arg.name
                out_arg = dp.out_arg.name
                if dp_name not in self._node_name_mapping:
                    self._node_name_mapping[dp_name] = str(len(self._node_name_mapping))
                    node_name = self._node_name_mapping[dp_name]
                    label = f"{{{dp_name}}}|{{<o_{out_arg}> {out_arg}}}"
                    self._g.add_node(
                        pydot.Node(name=node_name, label=label, shape="record", color="red")
                    )
                source = self._node_name_mapping[dp_name] + f":o_{out_arg}"
                target = self._node_name_mapping[name] + f":i_{in_arg}"
                self._g.add_edge(pydot.Edge(source, target))

    def _add_inputs(self, inputs: Mapping[str, Mapping[str, InParameter]]) -> None:
        if len(inputs) > 0:
            name = "inputs"
            self._add_name_to_mapping(name)
            outputs = self._format_arguments(inputs, "o")
            label = f"{{{{{outputs}}}}}"
            self._g.add_node(
                pydot.Node(
                    name=self._node_name_mapping[name], label=label, shape="record", color="red"
                )
            )
            for input, collection in inputs.items():
                source = self._node_name_mapping[name] + f":o_{input}"
                for entry in collection.values():
                    target = self._node_name_mapping[repr(entry.node)] + f":i_{entry.param.name}"
                    self._g.add_edge(pydot.Edge(source, target))

    def _add_outputs(self, outputs: Mapping[str, Mapping[str, OutParameter]]) -> None:
        if len(outputs) > 0:
            name = "outputs"
            self._add_name_to_mapping(name)
            inputs = self._format_arguments(outputs, "i")
            label = f"{{{{{inputs}}}}}"
            self._g.add_node(
                pydot.Node(
                    name=self._node_name_mapping[name], label=label, shape="record", color="red"
                )
            )
            for output, collection in outputs.items():
                target = self._node_name_mapping[name] + f":i_{output}"
                for entry in collection.values():
                    source = self._node_name_mapping[repr(entry.node)] + f":o_{entry.param.name}"
                    self._g.add_edge(pydot.Edge(source, target))

    def add_pipeline(self, pipeline: Pipeline) -> None:
        self._add_pipeline(pipeline.dag)
        self._add_inputs(pipeline.inputs)
        self._add_outputs(pipeline.outputs)

    def get_dot(self) -> pydot.Dot:  # type: ignore[no-any-unimported]
        return self._g


def dag_to_dot(dag: DAG) -> pydot.Dot:  # type: ignore[no-any-unimported]
    builder = DotBuilder()
    builder._add_pipeline(dag)
    return builder.get_dot()


def pipeline_to_dot(pipeline: Pipeline) -> pydot.Dot:  # type: ignore[no-any-unimported]
    builder = DotBuilder()
    builder.add_pipeline(pipeline)
    return builder.get_dot()


def dag_to_svg(dag: DAG) -> bytes:
    dot = dag_to_dot(dag)
    return dot.create(format="svg")


def display_dag(pipeline: Pipeline, format: str = "png", **kwds: Any) -> None:
    from IPython.display import SVG, Image, display  # type: ignore

    if format == "png":
        display_class = Image
    elif format == "svg":
        display_class = SVG
    else:
        raise ValueError(f"Unsupported format {format}. Supported formats are png and svg.")

    display(display_class(pipeline_to_dot(pipeline, **kwds).create(format=format)))
