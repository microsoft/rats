"""FrozenDict class.

Original source from https://stackoverflow.com/a/25332884 (MIT License)

"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, FrozenSet, Iterable, Mapping, Tuple, Type, TypeVar, cast

from omegaconf import OmegaConf

from ._frozendict import FrozenDict
from ._pipeline import PDependency, Pipeline, PNode, PNodeProperties, Provider
from ._processor import Processor, ProcessorInput, ProcessorOutput

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


class NoOp(Processor[T]):
    def process(self) -> T:
        return cast(T, {})


class HeadPipelineClient:
    @staticmethod
    def _build_head_pipeline_only(
        *pipelines: Pipeline[T, TI, TO],
        head_name: str = "head",
        props: PNodeProperties[T] = PNodeProperties(Provider(NoOp, OmegaConf.create())),
    ) -> Pipeline[T, TI, TO]:
        hnode = PNode(head_name)
        dependencies: Dict[PNode, FrozenSet[PDependency[TI, TO]]] = defaultdict(frozenset)
        for pipeline in pipelines:
            for ext_dp in pipeline.external_dependencies:
                dependencies[hnode] |= set((ext_dp,))  # aggregate all ext dependencies on the head
        return Pipeline(frozenset((hnode,)), FrozenDict(dependencies), FrozenDict({hnode: props}))

    @staticmethod
    def _interpose_head_pipeline_before_pipeline(
        head_pipeline: Pipeline[T, TI, TO], pipeline: Pipeline[T, TI, TO]
    ) -> Pipeline[T, TI, TO]:
        if len(head_pipeline) != 1:
            raise ValueError("head_pipeline must have a single node only.")
        hnode = set(head_pipeline.nodes).pop()  # pop unique head node
        dependencies = dict(pipeline.dependencies)  # copy dependencies from pipeline
        for start_node in pipeline.start_nodes:  # iterate over start nodes to change external dps
            for dp in pipeline.dependencies[start_node]:  # iterate over FrozenSet of dependencies
                if dp in pipeline.external_dependencies:  # remove old dependency & add new to head
                    dependencies[start_node] -= set((dp,))
                    dependencies[start_node] |= set((PDependency(hnode, dp.in_arg, dp.out_arg),))
        new_pipeline: Pipeline[T, TI, TO] = Pipeline(
            pipeline.nodes, FrozenDict(dependencies), pipeline.props
        )
        return new_pipeline + head_pipeline

    @classmethod
    def build_head_pipeline(
        cls,
        *pipelines: Pipeline[T, TI, TO],
        head_name: str = "head",
        props: PNodeProperties[T] = PNodeProperties(Provider(NoOp, OmegaConf.create())),
    ) -> Pipeline[T, TI, TO]:
        head_pipeline = cls._build_head_pipeline_only(*pipelines, head_name=head_name, props=props)
        return cls._interpose_head_pipeline_before_pipeline(
            head_pipeline, sum(pipelines, start=Pipeline())
        )


class TailPipelineClient:
    @staticmethod
    def build_tail_pipeline(
        *pipelines: Pipeline[T, TI, TO],
        tail_name: str = "tail",
        props: PNodeProperties[T] = PNodeProperties(Provider(NoOp, OmegaConf.create())),
        exclude: Tuple[str, ...] = (),
    ) -> Pipeline[T, TI, TO]:
        if len(pipelines) == 0:
            raise ValueError("Missing `pipelines` input argument.")

        node = PNode(tail_name)
        dependencies: DefaultDict[PNode, FrozenSet[PDependency[TI, TO]]] = defaultdict(frozenset)
        for pipeline in pipelines:
            for end_node in pipeline.end_nodes:
                outputs = ProcessorOutput.signature_from_provider(
                    pipeline.props[end_node].exec_provider
                )
                for out_arg in outputs.items():
                    if out_arg[0] not in exclude:
                        dependencies[node] |= set((PDependency(end_node, out_arg, out_arg),))
        return Pipeline(frozenset((node,)), FrozenDict(dependencies), FrozenDict({node: props}))


class ProcessorCommonInputsOutputs:
    @staticmethod
    def intersect_signatures(
        in_processor_type: Type[Processor[T]],
        out_processor_type: Type[Processor[T]],
    ) -> Tuple[FrozenDict[str, Type[Any]], FrozenDict[str, Type[Any]]]:
        in_sig = ProcessorInput.signature(in_processor_type)
        out_sig = ProcessorOutput.signature(out_processor_type)
        io: Tuple[Dict[str, Type[Any]], Dict[str, Type[Any]]] = ({}, {})
        for k in in_sig.keys() & out_sig.keys():
            if issubclass(out_sig[k], in_sig[k]):
                io[0][k] = in_sig[k]
                io[1][k] = out_sig[k]
        return (FrozenDict(io[0]), FrozenDict(io[1]))

    @staticmethod
    def get_common_dependencies_from_providers(
        node: PNode,
        in_provider: Provider[T],
        out_provider: Provider[T],
        node_hanging_dependencies: Iterable[PDependency[TI, TO]],
    ) -> FrozenSet[PDependency[TI, TO]]:
        sig = ProcessorCommonInputsOutputs.intersect_signatures(
            in_provider.processor_type, out_provider.processor_type
        )
        return frozenset(
            dp.set_node(node, (dp.in_arg[0], sig[1][dp.in_arg[0]]))  # propagate output subtype
            for dp in node_hanging_dependencies
            if dp.in_arg[0] in sig[0]  # if in_arg exists in out_provider
        )
