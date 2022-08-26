# type: ignore
# flake8: noqa
import pydot

from ..processors import Processor
from ..processors.base_dag import BaseDAG


def processor_to_dot(processor: Processor, node_to_color={}) -> pydot.Dot:
    if processor.is_dag():
        return dag_to_dot(processor, node_to_color)
    else:
        g = pydot.Dot("DAG", graph_type="digraph")
        inputs = "|".join(
            [f"<i_{port_name}> {port_name}" for port_name in processor.get_input_schema().keys()]
        )
        outputs = "|".join(
            [f"<o_{port_name}> {port_name}" for port_name in processor.get_output_schema().keys()]
        )
        node_name = processor.name
        color = node_to_color.get(node_name, "blue")
        label = f"{{{{{inputs}}}|{node_name}|{{{outputs}}}}}"
        g.add_node(pydot.Node(name="n", label=label, shape="Mrecord", color=color))
        return g


def dag_to_dot(dag: BaseDAG, node_to_color={}) -> pydot.Dot:
    g = pydot.Dot("DAG", graph_type="digraph")
    node_name_mapping = dict()
    if len(dag.input_edges) > 0:
        name = "inputs"
        node_name_mapping[name] = str(len(node_name_mapping))
        outputs = "|".join(
            [f"<{port_name}> {port_name}" for port_name in set(dag.input_edges.values())]
        )
        label = f"{{inputs|{{{outputs}}}}}"
        g.add_node(
            pydot.Node(name=node_name_mapping[name], label=label, shape="record", color="red")
        )
    for node_name, node in dag.nodes.items():
        name = f"n_{node_name}"
        node_name_mapping[name] = str(len(node_name_mapping))
        inputs = "|".join(
            [f"<i_{port_name}> {port_name}" for port_name in node.get_input_schema().keys()]
        )
        outputs = "|".join(
            [f"<o_{port_name}> {port_name}" for port_name in node.get_output_schema().keys()]
        )
        label = f"{{{{{inputs}}}|{node_name}:{node.name}|{{{outputs}}}}}"
        color = node_to_color.get(node_name, "blue")
        g.add_node(
            pydot.Node(name=node_name_mapping[name], label=label, shape="Mrecord", color=color)
        )
    if len(dag.output_edges) > 0:
        name = "outputs"
        node_name_mapping[name] = str(len(node_name_mapping))
        inputs = "|".join([f"<{port_name}> {port_name}" for port_name in dag.output_edges.keys()])
        label = f"{{{{{inputs}}}|{{outputs}}}}"
        g.add_node(
            pydot.Node(name=node_name_mapping[name], label=label, shape="record", color="red")
        )
    for input_port_address, input_port_name in dag.input_edges.items():
        source = node_name_mapping["inputs"] + f":{input_port_name}"
        target = (
            node_name_mapping[f"n_{input_port_address.node}"] + f":i_{input_port_address.port}"
        )
        g.add_edge(pydot.Edge(source, target))
    for input_port_address, output_port_address in dag.edges.items():
        source = (
            node_name_mapping[f"n_{output_port_address.node}"] + f":o_{output_port_address.port}"
        )
        target = (
            node_name_mapping[f"n_{input_port_address.node}"] + f":i_{input_port_address.port}"
        )
        g.add_edge(pydot.Edge(source, target))
    for output_port_name, output_port_address in dag.output_edges.items():
        source = (
            node_name_mapping[f"n_{output_port_address.node}"] + f":o_{output_port_address.port}"
        )
        target = node_name_mapping["outputs"] + f":{output_port_name}"
        g.add_edge(pydot.Edge(source, target))
    return g


def processor_to_svg(dag: BaseDAG, **kwds) -> bytes:
    dot = processor_to_dot(dag, **kwds)
    return dot.create(format="svg")
