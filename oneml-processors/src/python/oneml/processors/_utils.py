"""Utilities."""
from __future__ import annotations

from collections import defaultdict
from inspect import Parameter
from typing import AbstractSet, Any, Iterable, Mapping, TypedDict, TypeVar

from ._frozendict import frozendict
from ._pipeline import PDependency, Pipeline, PNode, PNodeProperties, Provider
from ._processor import DataArg, IProcessor, ProcessorInput, ProcessorOutput

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


EmptyDict = TypedDict("EmptyDict", {})


class NoOp(IProcessor[EmptyDict]):
    def process(self) -> EmptyDict:
        return EmptyDict()


class HeadPipelineClient:
    @staticmethod
    def _build_head_pipeline_only(
        *pipelines: Pipeline,
        head_name: str = "head",
        props: PNodeProperties[T] = PNodeProperties(Provider[T](NoOp)),
    ) -> Pipeline:
        hnode = PNode(head_name)
        dependencies: dict[PNode, AbstractSet[PDependency[Any, Any]]] = defaultdict(set)
        for pipeline in pipelines:
            for ext_dp in pipeline.external_dependencies:
                dependencies[hnode] |= set((ext_dp,))  # aggregate all ext dependencies on the head
        return Pipeline(set((hnode,)), dependencies, {hnode: props})

    @staticmethod
    def _interpose_head_pipeline_before_pipeline(
        head_pipeline: Pipeline, pipeline: Pipeline
    ) -> Pipeline:
        if len(head_pipeline) != 1:
            raise ValueError("head_pipeline must have a single node only.")
        hnode = set(head_pipeline.nodes).pop()  # pop unique head node
        dependencies = dict(pipeline.dependencies)  # copy dependencies from pipeline
        for start_node in pipeline.start_nodes:  # iterate over start nodes to change external dps
            for dp in pipeline.dependencies[start_node]:  # iterate over FrozenSet of dependencies
                if dp in pipeline.external_dependencies:  # remove old dependency & add new to head
                    dependencies[start_node] -= set((dp,))
                    dependencies[start_node] |= set((PDependency(hnode, dp.in_arg, dp.out_arg),))
        new_pipeline: Pipeline = Pipeline(pipeline.nodes, dependencies, pipeline.props)
        return new_pipeline + head_pipeline

    @classmethod
    def build_head_pipeline(
        cls,
        *pipelines: Pipeline,
        head_name: str = "head",
        props: PNodeProperties[T] = PNodeProperties(Provider[T](NoOp)),
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
        props: PNodeProperties[T] = PNodeProperties(Provider[T](NoOp)),
        exclude: AbstractSet[DataArg[TI]] = set(),
    ) -> Pipeline:
        if len(pipelines) == 0:
            raise ValueError("Missing `pipelines` input argument.")

        node = PNode(tail_name)
        dependencies: defaultdict[PNode, AbstractSet[PDependency[Any, Any]]] = defaultdict(set)
        for pipeline in pipelines:
            for end_node in pipeline.end_nodes:
                outputs = ProcessorOutput.signature_from_provider(
                    pipeline.props[end_node].exec_provider
                )
                for out_arg in outputs.values():
                    if out_arg not in exclude:
                        dependencies[node] |= set((PDependency(end_node, out_arg, out_arg),))
        return Pipeline(set((node,)), dependencies, {node: props})


class ProcessorCommonInputsOutputs:
    @staticmethod
    def intersect_signatures(
        in_provider: Provider[T], out_provider: Provider[T]
    ) -> Mapping[str, tuple[Parameter, DataArg[Any]]]:
        in_sig = ProcessorInput.signature_from_provider(in_provider)
        out_sig = ProcessorOutput.signature_from_provider(out_provider)
        io: dict[str, tuple[Parameter, DataArg[Any]]] = {}
        for k in in_sig.keys() & out_sig.keys():
            if issubclass(out_sig[k].annotation, in_sig[k].annotation):
                io[k] = (in_sig[k], out_sig[k])
        return frozendict(io)

    @staticmethod
    def get_common_dependencies_from_providers(
        node: PNode,
        in_provider: Provider[T],
        out_provider: Provider[T],
        node_hanging_dependencies: Iterable[PDependency[Any, Any]],
    ) -> AbstractSet[PDependency[Any, Any]]:
        sig = ProcessorCommonInputsOutputs.intersect_signatures(in_provider, out_provider)
        return frozenset(
            dp.set_node(node, dp.out_arg)  # propagate output subtype
            for dp in node_hanging_dependencies
            if dp.in_arg.key in sig  # if in_arg exists in common dependencies
        )
