import sys
from inspect import Parameter
from typing import Any, Dict, Literal, Mapping, TypeVar

import pydot

from ._pipeline import Pipeline
from ._processor import OutParameter, Provider
from ._utils import Annotations

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors


def dag_to_dot(pipeline: Pipeline) -> pydot.Dot:  # type: ignore[no-any-unimported]
    def in_signature_from_provider(provider: Provider[T]) -> Mapping[str, Parameter]:
        init_sig = Annotations.signature(provider.processor_type.__init__)
        proc_sig = Annotations.signature(provider.processor_type.process)
        if sys.version_info >= (3, 10):
            return init_sig | proc_sig
        else:
            return {**init_sig, **proc_sig}

    def out_signature_from_provider(provider: Provider[T]) -> Mapping[str, OutParameter]:
        return Annotations.get_return_annotation(provider.processor_type.process)

    def parse_arguments_from_provider(arguments: Mapping[str, Any], io: Literal["i", "o"]) -> str:
        return "|".join((f"<{io}_{arg}> {arg}" for arg in arguments.keys()))

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
            out_arg = dp.out_arg.name if dp.node else ""
            if dp_name not in node_name_mapping:
                node_name_mapping[dp_name] = str(len(node_name_mapping))
                node_name = node_name_mapping[dp_name]
                label = f"{{{dp_name}}}|{{<o_{out_arg}> {out_arg}}}"
                g.add_node(pydot.Node(name=node_name, label=label, shape="record", color="red"))
            source = node_name_mapping[dp_name] + f":o_{out_arg}"
            target = node_name_mapping[name] + f":i_{out_arg}"
            g.add_edge(pydot.Edge(source, target))

    return g


def dag_to_svg(pipeline: Pipeline) -> bytes:
    dot = dag_to_dot(pipeline)
    return dot.create(format="svg")
