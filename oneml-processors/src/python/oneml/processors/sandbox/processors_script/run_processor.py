#!/usr/bin/env python3
# type: ignore
# flake8: noqa

import sys
from typing import Dict, List

from oneml.processors import (
    DAG,
    DAGFlattener,
    DAGRunner,
    InputPortAddress,
    NodeName,
    OutputPortAddress,
    Processor,
    RunContext,
    SimpleNodeName,
    TopologicalSortDAGRunner,
    load_processor,
)

from .input_output import ReadProcessor, WriteProcessor


def build_wrapping_dag(processor: Processor, input_path: str, output_path: str) -> DAG:
    nodes: Dict[SimpleNodeName, Processor] = dict()
    edges: Dict[InputPortAddress, OutputPortAddress] = dict()
    processor_node_name = SimpleNodeName("processor")
    nodes[processor_node_name] = processor

    read_nodes: List[ReadProcessor] = []
    write_nodes: List[WriteProcessor] = []
    for input_port_name, inputPortDataType in processor.get_input_schema().items():
        read_node_name = SimpleNodeName(f"read:{input_port_name}")
        read_node = ReadProcessor(input_path, input_port_name, inputPortDataType)
        nodes[read_node_name] = read_node
        read_nodes.append(read_node)
        edges[InputPortAddress(processor_node_name, input_port_name)] = OutputPortAddress(
            read_node_name, "output"
        )
    for outputPortName, outputPortDataType in processor.get_output_schema().items():
        write_node_name = SimpleNodeName(f"write:{outputPortName}")
        write_node = WriteProcessor(output_path, outputPortName, outputPortDataType)
        nodes[write_node_name] = write_node
        write_nodes.append(write_node)
        edges[InputPortAddress(write_node_name, "input")] = OutputPortAddress(
            processor_node_name, outputPortName
        )
    dag = DAG(
        nodes=nodes,
        input_edges={},
        output_edges={},
        edges=edges,
    )
    return dag


def get_dag_flattener() -> DAGFlattener:
    return DAGFlattener()


def get_dag_runner() -> DAGRunner:
    return TopologicalSortDAGRunner(dag_modifiers=[get_dag_flattener().flatten])


def get_run_context(address: NodeName) -> RunContext:
    return RunContext(dag_runner=get_dag_runner(), identifier=address)


def main(argv: List[str] = sys.argv) -> None:
    if len(argv) != 5:
        raise ValueError(
            f"Expected four commandline arguments: <NodeName> <processor_path> <input_path> "
            f"<output_path>. Found: <{argv}>."
        )
    run_context = get_run_context(NodeName(argv[1]))
    processor = load_processor(argv[2])
    input_path = argv[3]
    output_path = argv[4]
    dag = build_wrapping_dag(processor, input_path, output_path)
    dag.process(run_context)
