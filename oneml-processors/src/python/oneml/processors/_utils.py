"""Utilities."""
from __future__ import annotations

from collections import defaultdict
from typing import AbstractSet, Any, Mapping

from ._orderedset import oset
from ._pipeline import PDependency, Pipeline, PNode, ProcessorProps
from ._processor import IProcess, OutParameter


class NoOp(IProcess):
    def process(self, **kwargs: Any) -> Mapping[str, Any]:
        return kwargs


class HeadPipelineClient:
    @staticmethod
    def _build_head_pipeline_only(
        *pipelines: Pipeline,
        props: ProcessorProps,
        head_name: str = "head",
    ) -> Pipeline:
        hnode = PNode(head_name)
        dependencies: dict[PNode, oset[PDependency]] = defaultdict(oset)
        for pipeline in pipelines:
            for ext_dp in pipeline.external_dependencies:
                dependencies[hnode] |= oset((ext_dp,))  # aggregate all ext dependencies
        return Pipeline({hnode: props}, dependencies)

    @staticmethod
    def _interpose_head_pipeline_before_pipeline(
        head_pipeline: Pipeline, pipeline: Pipeline
    ) -> Pipeline:
        if len(head_pipeline) != 1:
            raise ValueError("head_pipeline must have a single node only.")
        hnode = set(head_pipeline.nodes.keys()).pop()  # pop unique head node
        dependencies = dict(pipeline.dependencies)  # copy dependencies from pipeline
        for start_node in pipeline.start_nodes:  # iterate over start nodes to change external dps
            for dp in pipeline.dependencies[start_node]:  # iterate over FrozenSet of dependencies
                if dp in pipeline.external_dependencies:  # remove old dependency & add new to head
                    dependencies[start_node] -= set((dp,))
                    dependencies[start_node] |= set((PDependency(hnode, dp.in_arg, dp.out_arg),))
        new_pipeline: Pipeline = Pipeline(pipeline.nodes, dependencies)
        return new_pipeline + head_pipeline

    @classmethod
    def build_head_pipeline(
        cls,
        *pipelines: Pipeline,
        props: ProcessorProps,
        head_name: str = "head",
    ) -> Pipeline:
        head_pipeline = cls._build_head_pipeline_only(*pipelines, head_name=head_name, props=props)
        return cls._interpose_head_pipeline_before_pipeline(
            head_pipeline, sum(pipelines, start=Pipeline())
        )


class TailPipelineClient:
    @staticmethod
    def build(
        *pipelines: Pipeline,
        exclude: AbstractSet[str] = set(),
    ) -> Pipeline:
        if len(pipelines) == 0:
            raise ValueError("Missing `pipelines` input argument.")

        node = PNode("tail")
        ra: dict[str, OutParameter] = {}
        dependencies: defaultdict[PNode, oset[PDependency]] = defaultdict(oset)
        for pipeline in pipelines:
            for end_node in pipeline.end_nodes:
                for out_param in pipeline.nodes[end_node].ret.values():
                    if out_param.name not in exclude:
                        in_param = out_param.to_inparameter()
                        ra[in_param.name] = OutParameter(in_param.name, in_param.annotation)
                        dependencies[node] |= oset((PDependency(end_node, in_param, out_param),))

        props = ProcessorProps(NoOp, return_annotation=ra)
        return Pipeline({node: props}, dependencies)
