from typing import Any, Dict, Literal, Mapping, Type, TypeVar

import pydot

from ._pipeline import Pipeline
from ._processor import Provider
from ._utils import ProcessorInput, ProcessorOutput

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


def dag_to_dot(pipeline: Pipeline[T, TI, TO]) -> pydot.Dot:  # type: ignore[no-any-unimported]
    def in_signature_from_provider(provider: Provider[T]) -> Mapping[str, Type[Any]]:
        return ProcessorInput.signature_from_provider(provider)

    def out_signature_from_provider(provider: Provider[T]) -> Mapping[str, Type[Any]]:
        return ProcessorOutput.signature_from_provider(provider)

    def parse_arguments_from_provider(
        arguments: Mapping[str, Type[Any]], io: Literal["i", "o"]
    ) -> str:
        return "|".join((f"<{io}_{k}> {k}" for k in arguments.keys()))

    g = pydot.Dot("DAG", graph_type="digraph")
    node_name_mapping: Dict[str, str] = {}

    for node in pipeline.nodes:
        name = repr(node)
        node_name_mapping[name] = str(len(node_name_mapping))
        in_arguments = in_signature_from_provider(pipeline.props[node].exec_provider)
        inputs = parse_arguments_from_provider(in_arguments, "i")
        out_arguments = out_signature_from_provider(pipeline.props[node].exec_provider)
        outputs = parse_arguments_from_provider(out_arguments, "o")

        label = f"{{{{{inputs}}}|{name}|{{{outputs}}}}}"
        node_name = node_name_mapping[name]
        g.add_node(pydot.Node(name=node_name, label=label, shape="Mrecord", color="blue"))

    for node, dps in pipeline.dependencies.items():
        name = repr(node)
        for dp in dps:
            dp_name = repr(dp.node)
            out_arg = dp.out_arg[0] if dp.out_arg else dp.in_arg[0] if dp.node else ""
            if dp_name not in node_name_mapping:
                node_name_mapping[dp_name] = str(len(node_name_mapping))
                node_name = node_name_mapping[dp_name]
                label = f"{{{dp_name}}}|{{<o_{out_arg}> {out_arg}}}"
                g.add_node(pydot.Node(name=node_name, label=label, shape="record", color="red"))
            source = node_name_mapping[dp_name] + f":o_{out_arg}"
            target = node_name_mapping[name] + f":i_{out_arg}"
            g.add_edge(pydot.Edge(source, target))

    return g


def dag_to_svg(pipeline: Pipeline[T, TI, TO]) -> bytes:
    dot = dag_to_dot(pipeline)
    return dot.create(format="svg")
