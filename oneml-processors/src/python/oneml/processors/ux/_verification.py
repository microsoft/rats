from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..dag import DAG
    from ._pipeline import (
        InCollections,
        InEntry,
        Inputs,
        OutCollections,
        OutEntry,
        Outputs,
        UPipeline,
    )


def _verify_dag_integrity(dag: DAG) -> None:
    for node, dp in dag.dependencies.items():
        if node not in dag.nodes:
            raise ValueError(f"Dependency target node {node} is not in the DAG.")
        for d in dp:
            if d.node not in dag.nodes:
                raise ValueError(f"Dependency source node {d.node} is not in the DAG.")
            if d.in_arg.name not in dag.nodes[node].inputs:
                raise ValueError(
                    f"Input parameter {d.in_arg.name} of dependecy {d} is not in target node {node}."
                )
            if d.out_arg is None:
                raise ValueError(f"Output parameter is not specified for {d}.")
            if d.out_arg.name not in dag.nodes[d.node].outputs:
                raise ValueError(
                    f"Output parameter {d.out_arg.name} of dependency {d} is not in source node {d.node}."
                )


def _verify_pipeline_name(name: str, dag: DAG) -> None:
    for node in dag.nodes:
        first_part_for_node_path = str(node).lstrip("/").split("/", 1)[0]
        if first_part_for_node_path != name:
            raise ValueError(f"First part of node path {node} is not pipeline name {name}.")


def _verify_input_entry(in_name: str, in_entry: InEntry[Any], dag: DAG) -> None:
    if len(in_entry) == 0:
        raise ValueError(f"Input parameter {in_name} does not point to any node.")
    for in_param in in_entry:
        if in_param.node not in dag.nodes:
            raise ValueError(
                f"Input parameter {in_name} points to node {in_param.node} that is not in the DAG."
            )
        if in_param.param.name not in dag.nodes[in_param.node].inputs:
            raise ValueError(
                f"Input parameter {in_name} points to node param {in_param.param.name} that is not in target node {in_param.node}."
            )


def _verify_pipeline_inputs(inputs: Inputs, dag: DAG) -> None:
    for in_name, in_entry in inputs._asdict().items():
        _verify_input_entry(in_name, in_entry, dag)


def _verify_pipeline_in_collections(in_collections: InCollections, dag: DAG) -> None:
    for col_name, collection in in_collections._asdict().items():
        for in_name, in_entry in collection._asdict().items():
            _verify_input_entry(f"{col_name}.{in_name}", in_entry, dag)


def _verify_output_entry(out_name: str, out_entry: OutEntry[Any], dag: DAG) -> None:
    # Is there a legit situation where out_entry has more than one element?
    # If not, then maybe we should change the type of out_entry to OutParam?
    if len(out_entry) != 1:
        raise ValueError(
            f"Output parameters should point to exactly one node. {out_name} points to {len(out_entry)}."
        )
    for out_param in out_entry:
        if out_param.node not in dag.nodes:
            raise ValueError(
                f"Output parameter {out_name} points to node {out_param.node} that is not in the DAG."
            )
        if out_param.param.name not in dag.nodes[out_param.node].outputs:
            raise ValueError(
                f"Output parameter {out_name} points to node param {out_param.param.name} that is not in target node {out_param.node}."
            )


def _verify_pipeline_outputs(outputs: Outputs, dag: DAG) -> None:
    for out_name, out_entry in outputs._asdict().items():
        _verify_output_entry(out_name, out_entry, dag)


def _verify_pipeline_out_collections(out_collections: OutCollections, dag: DAG) -> None:
    for col_name, collection in out_collections._asdict().items():
        for out_name, out_entry in collection._asdict().items():
            _verify_output_entry(f"{col_name}.{out_name}", out_entry, dag)


def verify_pipeline_integrity(pipeline: UPipeline) -> None:
    _verify_dag_integrity(pipeline._dag)
    _verify_pipeline_name(pipeline.name, pipeline._dag)
    _verify_pipeline_inputs(pipeline.inputs, pipeline._dag)
    _verify_pipeline_in_collections(pipeline.in_collections, pipeline._dag)
    _verify_pipeline_outputs(pipeline.outputs, pipeline._dag)
    _verify_pipeline_out_collections(pipeline.out_collections, pipeline._dag)
    return
