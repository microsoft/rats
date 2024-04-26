from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import count
from typing import TYPE_CHECKING, Any, Literal

import pydot

if TYPE_CHECKING:
    from ..ux._pipeline import InPort, Inputs, OutPort, Outputs, UPipeline
    from ._dag import DAG, DagNode


class DotBuilder:
    _g: pydot.Dot
    _node_name_mapping: dict[str, str]
    _include_optional: bool
    _first_distinct_level: int

    def __init__(self, include_optional: bool = True) -> None:
        self._g = pydot.Dot("DAG", graph_type="digraph")
        self._node_name_mapping = {}
        self._include_optional = include_optional
        self._first_distinct_level = 0

    def _get_io_tag(self, io: Literal["i", "o"], port_name: str) -> str:
        sanitized = port_name.replace("_", "__").replace(".", "_")
        return f"{io}_{sanitized}"

    def _format_arguments(self, io: Literal["i", "o"], arguments: Iterable[str]) -> str:
        return "|".join(f"<{self._get_io_tag(io, arg)}> {arg}" for arg in sorted(arguments))

    def _format_i_arguments(self, arguments: Iterable[str]) -> str:
        return self._format_arguments("i", arguments)

    def _format_o_arguments(self, arguments: Iterable[str]) -> str:
        return self._format_arguments("o", arguments)

    def _get_port_tag(self, io: Literal["i", "o"], node_name: str, port_name: str) -> str:
        return f"{self._node_name_mapping[node_name]}:{self._get_io_tag(io, port_name)}"

    def _get_i_port_tag(self, node_name: str, port_name: str) -> str:
        return self._get_port_tag("i", node_name, port_name)

    def _get_o_port_tag(self, node_name: str, port_name: str) -> str:
        return self._get_port_tag("o", node_name, port_name)

    def _add_name_to_mapping(self, name: str) -> None:
        if name not in self._node_name_mapping:
            self._node_name_mapping[name] = str(len(self._node_name_mapping))

    def _node_label(self, node: DagNode) -> str:
        tokens = repr(node).split("/")
        if self._first_distinct_level == len(tokens) - 1:
            return tokens[-1]
        return f"{tokens[self._first_distinct_level]}..{tokens[-1]}"

    def _add_pipeline(self, dag: DAG) -> None:
        for node in dag.nodes:
            node_label = self._node_label(node)
            name = repr(node)
            self._add_name_to_mapping(name)
            in_arguments = tuple(k.name for k in dag.nodes[node].inputs.values())
            inputs = self._format_i_arguments(in_arguments)
            out_arguments = tuple(k.name for k in dag.nodes[node].outputs.values())
            outputs = self._format_o_arguments(out_arguments)

            label = f"{{{{{inputs}}}|{node_label}|{{{outputs}}}}}"
            node_name = self._node_name_mapping[name]
            self._g.add_node(
                pydot.Node(name=node_name, label=label, shape="Mrecord", color="blue")
            )

        for node, dps in dag.dependencies.items():
            name = repr(node)
            for dp in dps:
                if dp.in_arg.required or self._include_optional:
                    dp_name = repr(dp.node)
                    in_arg = dp.in_arg.name
                    out_arg = dp.out_arg.name
                    source = self._get_o_port_tag(dp_name, out_arg)
                    target = self._get_i_port_tag(name, in_arg)
                    self._g.add_edge(
                        pydot.Edge(
                            source, target, style="solid" if dp.in_arg.required else "dashed"
                        )
                    )

    def _add_inputs(self, inputs: Inputs) -> None:
        def add_entry(source: str, entry: InPort[Any]) -> None:
            for p in entry:
                target = self._get_i_port_tag(repr(p.node), p.param.name)
                self._g.add_edge(
                    pydot.Edge(source, target, style="solid" if p.required else "dashed")
                )

        def add_inputs_node(
            ro: Literal["required", "optional"], entries: Mapping[str, InPort[Any]]
        ) -> None:
            name = f"{ro}_inputs"
            self._add_name_to_mapping(name)

            outputs = self._format_o_arguments(entries)
            label = f"{{{{{outputs}}}}}"
            self._g.add_node(
                pydot.Node(
                    name=self._node_name_mapping[name],
                    label=label,
                    shape="record",
                    color="red",
                    style="solid" if ro == "required" else "dashed",
                )
            )
            for entry_name, entry in entries.items():
                source = self._get_o_port_tag(name, entry_name)
                add_entry(source, entry)

        entries = inputs._asdict()
        required = {k: v for k, v in entries.items() if v.required}
        optional = {k: v for k, v in entries.items() if v.optional}
        if len(required) > 0:
            add_inputs_node("required", required)
        if len(optional) > 0 and self._include_optional:
            add_inputs_node("optional", optional)

    def _add_outputs(self, outputs: Outputs) -> None:
        def add_entry(entry: OutPort[Any], target: str) -> None:
            for p in entry:
                source = self._get_o_port_tag(repr(p.node), p.param.name)
                self._g.add_edge(pydot.Edge(source, target))

        if len(outputs) > 0:
            entries = outputs._asdict()
            name = "outputs"
            self._add_name_to_mapping(name)

            inputs = self._format_i_arguments(entries)
            label = f"{{{{{inputs}}}}}"
            self._g.add_node(
                pydot.Node(
                    name=self._node_name_mapping[name], label=label, shape="record", color="red"
                )
            )
            for entry_name, entry in entries.items():
                target = self._get_i_port_tag(name, entry_name)
                add_entry(entry, target)

    def _find_first_distinct_level(self, dag: DAG) -> None:
        if len(dag.nodes) <= 1:
            return
        node_name_tokens = [repr(node).split("/") for node in dag.nodes]
        for i in count():
            tokens_at_level = set([tokens[i] for tokens in node_name_tokens])
            if len(tokens_at_level) > 1:
                self._first_distinct_level = i
                return

    def add_pipeline(self, pipeline: UPipeline) -> None:
        self._find_first_distinct_level(pipeline._dag)
        self._add_pipeline(pipeline._dag)
        self._add_inputs(pipeline.inputs)
        self._add_outputs(pipeline.outputs)

    def get_dot(self) -> pydot.Dot:
        return self._g


def dag_to_dot(dag: DAG, include_optional: bool = True) -> pydot.Dot:
    builder = DotBuilder(include_optional=include_optional)
    builder._add_pipeline(dag)
    return builder.get_dot()


def pipeline_to_dot(pipeline: UPipeline, include_optional: bool = True) -> pydot.Dot:
    builder = DotBuilder(include_optional=include_optional)
    builder.add_pipeline(pipeline)
    return builder.get_dot()


def dag_to_svg(dag: DAG, **kwds: Any) -> str:
    dot = dag_to_dot(dag, **kwds)
    return dot.create(format="svg")


def display_dag(pipeline: UPipeline, format: str = "png", **kwds: Any) -> None:
    from IPython.display import SVG, Image, display

    if format == "png":
        display_class = Image
    elif format == "svg":
        display_class = SVG
    else:
        raise ValueError(f"Unsupported format {format}. Supported formats are png and svg.")

    display(display_class(pipeline_to_dot(pipeline, **kwds).create(format=format)))
