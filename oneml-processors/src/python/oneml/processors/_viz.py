from typing import Any, Dict, Literal, Mapping

import pydot

from ._pipeline import Pipeline


def dag_to_dot(pipeline: Pipeline) -> pydot.Dot:  # type: ignore[no-any-unimported]
    def parse_arguments(arguments: Mapping[str, Any], io: Literal["i", "o"]) -> str:
        return "|".join((f"<{io}_{arg}> {arg}" for arg in arguments.keys()))

    g = pydot.Dot("DAG", graph_type="digraph")
    node_name_mapping: Dict[str, str] = {}

    for node in pipeline.nodes:
        name = repr(node)
        node_name_mapping[name] = str(len(node_name_mapping))
        in_arguments = pipeline.nodes[node].sig
        inputs = parse_arguments(in_arguments, "i")
        out_arguments = pipeline.nodes[node].ret
        outputs = parse_arguments(out_arguments, "o")

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
