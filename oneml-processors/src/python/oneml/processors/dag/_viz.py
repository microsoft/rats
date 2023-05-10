from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Literal, Mapping, Tuple

import pydot

if TYPE_CHECKING:
    from ..ux._pipeline import (
        PE,
        InCollections,
        InEntry,
        Inputs,
        IOCollections,
        OutCollections,
        OutEntry,
        Outputs,
        ParamCollection,
        Pipeline,
    )
    from ._dag import DAG


class DotBuilder:
    _g: pydot.Dot  # type: ignore[no-any-unimported]
    _node_name_mapping: dict[str, str]

    def __init__(self) -> None:
        self._g = pydot.Dot("DAG", graph_type="digraph")
        self._node_name_mapping = {}

    def _get_io_tag(self, io: Literal["i", "o"], port_name: str) -> str:
        sanitized = port_name.replace("_", "__").replace(".", "_")
        return f"{io}_{sanitized}"

    def _format_arguments(self, io: Literal["i", "o"], arguments: Iterable[str]) -> str:
        return "|".join((f"<{self._get_io_tag(io, arg)}> {arg}" for arg in sorted(arguments)))

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

    def _add_pipeline(self, dag: DAG) -> None:
        for node in dag.nodes:
            processor_name = node.name.split("/")[-1]
            name = repr(node)
            self._add_name_to_mapping(name)
            in_arguments = tuple(k.name for k in dag.nodes[node].inputs.values())
            inputs = self._format_i_arguments(in_arguments)
            out_arguments = tuple(k.name for k in dag.nodes[node].outputs.values())
            outputs = self._format_o_arguments(out_arguments)

            label = f"{{{{{inputs}}}|{processor_name}|{{{outputs}}}}}"
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
                source = self._get_o_port_tag(dp_name, out_arg)
                target = self._get_i_port_tag(name, in_arg)
                self._g.add_edge(
                    pydot.Edge(source, target, style="solid" if dp.in_arg.required else "dashed")
                )

    def _get_io_entries(
        self, io: ParamCollection[PE], io_collections: IOCollections[ParamCollection[PE]]
    ) -> Iterable[Tuple[str, PE]]:
        for entry_name, entry in io.items():
            yield entry_name, entry
        for collection_name, entry_collection in io_collections.items():
            for entry_name, entry in entry_collection.items():
                yield f"{collection_name}.{entry_name}", entry

    def _add_inputs(self, inputs: Inputs, in_collections: InCollections) -> None:
        def add_entry(source: str, entry: InEntry) -> None:
            for p in entry:
                target = self._get_i_port_tag(repr(p.node), p.param.name)
                self._g.add_edge(
                    pydot.Edge(source, target, style="solid" if p.required else "dashed")
                )

        def add_inputs_node(
            ro: Literal["required", "optional"], entries: Mapping[str, InEntry]
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

        entries = dict(self._get_io_entries(inputs, in_collections))
        required = {k: v for k, v in entries.items() if v.required}
        optional = {k: v for k, v in entries.items() if v.optional}
        if len(required) > 0:
            add_inputs_node("required", required)
        if len(optional) > 0:
            add_inputs_node("optional", optional)

    def _add_outputs(self, outputs: Outputs, out_collections: OutCollections) -> None:
        def add_entry(entry: OutEntry, target: str) -> None:
            for p in entry:
                source = self._get_o_port_tag(repr(p.node), p.param.name)
                self._g.add_edge(pydot.Edge(source, target))

        if len(outputs) > 0 or len(out_collections) > 0:
            entries = dict(self._get_io_entries(outputs, out_collections))
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

    def add_pipeline(self, pipeline: Pipeline) -> None:
        self._add_pipeline(pipeline._dag)
        self._add_inputs(pipeline.inputs, pipeline.in_collections)
        self._add_outputs(pipeline.outputs, pipeline.out_collections)

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
