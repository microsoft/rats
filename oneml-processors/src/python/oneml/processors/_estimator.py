from typing import AbstractSet, Any, Mapping, TypeVar

from ._pipeline import IExpandPipeline, IProcessorProps, Namespace, PDependency, Pipeline, PNode
from ._utils import TailPipelineClient

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)


class EstimatorPipeline(Pipeline):
    def __init__(
        self,
        nodes: Mapping[PNode, IProcessorProps],
        dependencies: Mapping[PNode, AbstractSet[PDependency]],
    ) -> None:
        super().__init__(nodes, dependencies)
        train_ns, eval_ns = Namespace("train"), Namespace("eval")
        if any(
            # if not every namespace is contained at least in a start_node in every pipeline
            not any(ns in node for node in self.nodes)
            for ns in (train_ns, eval_ns)
        ):
            raise Exception("Pipeline should contain train & eval namespaces in start nodes.")


class EstimatorPipelineFromTrainAndEval(IExpandPipeline):
    _train_pipeline: Pipeline
    _eval_pipeline: Pipeline

    def __init__(self, train_pipeline: Pipeline, eval_pipeline: Pipeline) -> None:
        super().__init__()
        self._train_pipeline = train_pipeline
        self._eval_pipeline = eval_pipeline

    def expand(self) -> EstimatorPipeline:
        train_ns, eval_ns = Namespace("train"), Namespace("eval")
        new_train = self._train_pipeline.decorate(train_ns)
        new_eval = self._eval_pipeline.decorate(eval_ns)
        # placeholder for external dependencies
        tail: Pipeline = TailPipelineClient.build_tail_pipeline(new_train, new_eval)
        new_pipeline = new_train + new_eval + tail

        new_dependencies = dict(new_pipeline.dependencies)
        for node in self._eval_pipeline.nodes:
            # decorate old node names with new decorated names
            # train_node = node.decorate(train_ns)
            eval_node = node.decorate(eval_ns)

            # add dependency from train to eval node if they are hanging dependencies
            # and if they share common inputs & outputs
            # hanging_dependencies = new_eval.dependencies[eval_node] & new_eval.hanging_dependencies
            # if hanging_dependencies:
            #     common_IO: AbstractSet[
            #         PDependency
            #     ] = ProcessorCommonInputsOutputs.get_common_dependencies_from_providers(
            #         train_node,
            #         new_eval.props[eval_node].exec_provider,
            #         new_train.props[train_node].exec_provider,
            #         node_hanging_dependencies=hanging_dependencies,
            #     )
            #     common_io_args = set(dp.in_arg for dp in common_IO)
            #     new_dependencies[eval_node] -= set(
            #         dp for dp in new_dependencies[eval_node] if dp.in_arg in common_io_args
            #     )
            #     new_dependencies[eval_node] |= common_IO

            # update external train dependencies on eval nodes if existing
            new_dependencies[eval_node] = frozenset(
                dp.decorate(train_ns) if dp.node and dp.node in self._train_pipeline else dp
                for dp in new_dependencies[eval_node]
            )
            new_pipeline = new_pipeline.set_dependencies(eval_node, new_dependencies[eval_node])

        return EstimatorPipeline(new_pipeline.nodes, new_pipeline.dependencies)


class WrapEstimatorPipeline:
    @staticmethod
    def wrap_estimator_pipeline_in_namespace(pipeline: EstimatorPipeline, name: str) -> Pipeline:
        new_pipeline = pipeline.decorate(Namespace(name))
        if len(new_pipeline.end_nodes) > 1:
            tail_pipeline = TailPipelineClient.build_tail_pipeline(pipeline)  # tail pipeline only
            new_pipeline += tail_pipeline
        return EstimatorPipeline(new_pipeline.nodes, new_pipeline.dependencies)


class SequentialEstimators(IExpandPipeline):
    _first_pipeline: EstimatorPipeline
    _second_pipeline: EstimatorPipeline

    def __init__(
        self,
        first_pipeline: EstimatorPipeline,
        second_pipeline: EstimatorPipeline,
    ) -> None:
        super().__init__()
        self._first_pipeline = first_pipeline
        self._second_pipeline = second_pipeline

    def expand(self) -> EstimatorPipeline:
        new_pipeline = self._first_pipeline + self._second_pipeline
        return EstimatorPipeline(new_pipeline.nodes, new_pipeline.dependencies)
