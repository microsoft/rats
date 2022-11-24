"""Utilities."""
from __future__ import annotations

from collections import defaultdict
from typing import AbstractSet, Any, Mapping

from ..utils import orderedset
from ._dag import DAG, DagDependency, DagNode, ProcessorProps
from ._processor import IProcess


class NoOp(IProcess):
    def process(self, **kwargs: Any) -> Mapping[str, Any]:
        return kwargs


class HeadPipelineClient:
    @staticmethod
    def _build_head_pipeline_only(
        *dags: DAG,
        props: ProcessorProps,
        head_name: str = "head",
    ) -> DAG:
        hnode = DagNode(head_name)
        dependencies: dict[DagNode, orderedset[DagDependency]] = defaultdict(orderedset)
        for dag in dags:
            for ext_dp in dag.external_dependencies.values():
                dependencies[hnode] |= ext_dp  # aggregate all ext dependencies on the head
        return DAG({hnode: props}, dependencies)

    @staticmethod
    def _interpose_head_pipeline_before_pipeline(head_pipeline: DAG, dag: DAG) -> DAG:
        if len(head_pipeline) != 1:
            raise ValueError("head_pipeline must have a single node only.")
        hnode = set(head_pipeline.nodes.keys()).pop()  # pop unique head node
        dependencies = dict(dag.dependencies)  # copy dependencies from dag
        for root_node in dag.root_nodes:  # iterate over start nodes to change external dps
            for dp in dag.dependencies[root_node]:  # iterate over FrozenSet of dependencies
                if dp in dag.external_dependencies[root_node]:
                    dependencies[root_node] -= set((dp,))  # remove old dps & add new to head
                    dependencies[root_node] |= set((DagDependency(hnode, dp.in_arg, dp.out_arg),))
        new_pipeline = DAG(dag.nodes, dependencies)
        return new_pipeline + head_pipeline

    @classmethod
    def build_head_pipeline(
        cls,
        *dags: DAG,
        props: ProcessorProps,
        head_name: str = "head",
    ) -> DAG:
        head_pipeline = cls._build_head_pipeline_only(*dags, head_name=head_name, props=props)
        return cls._interpose_head_pipeline_before_pipeline(head_pipeline, sum(dags, start=DAG()))


class TailPipelineClient:
    @staticmethod
    def build(
        *dags: DAG,
        exclude: AbstractSet[str] = set(),
    ) -> DAG:
        if len(dags) == 0:
            raise ValueError("Missing `dags` inputs argument.")

        node = DagNode("tail")
        ra: dict[str, type] = {}
        dependencies: defaultdict[DagNode, orderedset[DagDependency]] = defaultdict(orderedset)
        for dag in dags:
            for end_node in dag.leaf_nodes:
                for out_param in dag.nodes[end_node].outputs.values():
                    if out_param.name not in exclude:
                        in_param = out_param.to_inparameter()
                        ra[in_param.name] = in_param.annotation
                        dependencies[node] |= orderedset(
                            (DagDependency(end_node, in_param, out_param),)
                        )

        props = ProcessorProps(NoOp, return_annotation=ra)
        return DAG({node: props}, dependencies)
