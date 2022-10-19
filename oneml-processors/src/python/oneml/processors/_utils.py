"""Utilities."""
from __future__ import annotations

from collections import defaultdict
from typing import AbstractSet, Any, TypedDict

from ._pipeline import IProcessorProps, PDependency, Pipeline, PNode, ProcessorProps
from ._processor import IProcess

NoOpOutput = TypedDict("NoOpOutput", {}, total=False)


class NoOp(IProcess):
    def process(self, **kwargs: Any) -> NoOpOutput:
        return NoOpOutput(**kwargs)  # type: ignore[misc]


class HeadPipelineClient:
    @staticmethod
    def _build_head_pipeline_only(
        *pipelines: Pipeline,
        head_name: str = "head",
        props: IProcessorProps = ProcessorProps(NoOp),
    ) -> Pipeline:
        hnode = PNode(head_name)
        dependencies: dict[PNode, AbstractSet[PDependency]] = defaultdict(set)
        for pipeline in pipelines:
            for ext_dp in pipeline.external_dependencies:
                dependencies[hnode] |= set((ext_dp,))  # aggregate all ext dependencies on the head
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
        head_name: str = "head",
        props: IProcessorProps = ProcessorProps(NoOp),
    ) -> Pipeline:
        head_pipeline = cls._build_head_pipeline_only(*pipelines, head_name=head_name, props=props)
        return cls._interpose_head_pipeline_before_pipeline(
            head_pipeline, sum(pipelines, start=Pipeline())
        )


class TailPipelineClient:
    @staticmethod
    def build_tail_pipeline(
        *pipelines: Pipeline,
        tail_name: str = "tail",
        props: IProcessorProps = ProcessorProps(NoOp),
        exclude: AbstractSet[str] = set(),
    ) -> Pipeline:
        if len(pipelines) == 0:
            raise ValueError("Missing `pipelines` input argument.")

        node = PNode(tail_name)
        dependencies: defaultdict[PNode, AbstractSet[PDependency]] = defaultdict(set)
        for pipeline in pipelines:
            for end_node in pipeline.end_nodes:
                for out_param in pipeline.nodes[end_node].ret.values():
                    if out_param.name not in exclude:
                        in_param = out_param.to_inparameter()
                        dependencies[node] |= set((PDependency(end_node, in_param, out_param),))
        return Pipeline({node: props}, dependencies)
