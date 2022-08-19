from __future__ import annotations

import logging

from oneml.lorenzo.pipelines3._example._di_container import Pipeline3DiContainer
from oneml.lorenzo.pipelines3._example._gui import DagSvg, DagVisualizer, DotDag
from oneml.pipelines.building import PipelineBuilderClient, PipelineBuilderFactory
from oneml.lorenzo.pipelines3._example3._sample_steps import ProduceExampleSamplesRunner, \
    LogExampleSamplesRunner
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session._session_data_client import IManagePipelineData

logger = logging.getLogger(__name__)


class TinyPipelineExample:

    def do_it(self) -> None:
        builder = PipelineBuilderFactory().get_instance()

        builder.add_node(builder.node("hello"))
        builder.add_executable(
            # TODO: make this less repetitive and error prone :)
            builder.node("hello"),
            ProduceExampleSamplesRunner(builder.node("hello")),
        )

        builder.add_node(builder.node("world"))
        builder.add_dependency(builder.node("world"), builder.node("hello"))
        builder.add_executable(
            # TODO: make this less repetitive and error prone :)
            builder.node("world"),
            LogExampleSamplesRunner(input_node=builder.node("hello")),
        )

        pipeline_client = builder.build()
        session_factory = builder.get_session_client_factory()

        session_client = session_factory.get_instance(pipeline_client)
        session = session_client.pipeline_session_client()
        session.run()

        # self.do_again(session_client.pipeline_data_client())

    def do_again(self, proxy_storage: IManagePipelineData) -> None:
        factory = PipelineBuilderFactory()
        builder_client = factory.get_instance()

        dag = builder_client.get_dag_client()
        root = builder_client.get_namespace_client()
        executables_client = builder_client.get_executables_client()

        dag.add_node(root.node("world"))
        # dag.add_dependency(root.node("world"), root.node("hello"))
        executables_client.add_executable(
            root.node("world"),
            LogExampleSamplesRunner(input_node=root.node("hello")),
        )

        pipeline_client = dag.build()
        session_factory = builder_client.get_session_client_factory()

        session_components = session_factory.get_instance_with_external_data(
            pipeline_client=pipeline_client,
            external_storage=proxy_storage,
            external_nodes=(root.node("hello"),)
        )
        session = session_components.pipeline_session_client()
        session.run()

    # def do_it_1(self) -> None:
    #     pipeline_builder = self._builder_client.dag()
    #     root = self._builder_client.namespace_client()
    #     multiplexer = self._builder_client.multiplex_client()
    #
    #     pipeline_builder.add_node(root.node("hello"))
    #     pipeline_builder.add_executable(
    #         root.node("hello"),
    #         ContextualCallableExecutable[PipelineNode](
    #             context=root.node("hello"),
    #             callback=lambda context: print(context)),
    #     )
    #
    #     # users = multiplexer.get_instance(root, ["bob", "mike", "sam"])
    #     # pipeline_builder.add_nodes(users.nodes("world"))
    #     # users.add_external_dependency("world", root.node("hello"))
    #     # users.add_executable(
    #     #     "world", CallableMultiExecutable(lambda node: logger.info(f"hello from node: {node}")))
    #
    #     # MOVE FROM BUILDER TO PIPELINE
    #     pipeline_components: PipelineComponents = pipeline_builder.build()
    #
    #     # MOVE FROM PIPELINE TO SESSION
    #     # TODO: insert a session components piece!
    #     session_factory = PipelineSessionComponentsFactory()
    #
    #     session_components = session_factory.get_instance(pipeline_components)
    #     session = session_components.pipeline_session_client()
    #     session.run()
    #
    #     # samples = pipeline_data_client.get_data(root.node("hello"), PipelineDataNode[ExampleSamples]("example-samples"))
    #     # logger.info(samples.samples())
    #
    #     ###############
    #
    #     dot_dag = DotDag(
    #         node_client=pipeline_components.node_client(),
    #         dependencies_client=pipeline_components.node_dependencies_client(),
    #         node_state_client=session_components.node_state_client(),
    #     )
    #     svg_client = DagSvg(dot_dag=dot_dag)
    #     viz = DagVisualizer(svg_client=svg_client)
    #     viz.execute()


def _render_tiny_pipeline() -> None:
    di_container = Pipeline3DiContainer(args=tuple())
    di_container._logging_client().configure_logging()

    ##############
    """
    CONFUSING BITS!
    - We have a pipeline builder responsible for creation of PipelineBuilderClient
    - Use builder components to define a pipeline
    - call PipelineBuilderClient.pipeline_components() to get PipelineComponents
    - PipelineComponents is responsible for providing access to pipeline details
    - call PipelineComponents.session_components() to get PipelineSessionComponents
    - PipelineSessionComponents is responsible for providing access to pipeline session details
    - call PipelineSessionComponents.session_client() to get IRunnablePipelineSession
    - IRunnablePipelineSession progresses a session from STARTED state to COMPLETED state
    - IRunnablePipelineSession.run() loops calls to a tickable pipeline ITickablePipelineFrame
    - ITickablePipelineFrame is responsible for performing the work of a single frame
        - has access to the various frame commands
        - PromoteRegisteredNodesCommand queues REGISTERED nodes
        - PromoteQueuedNodesCommand validates dependencies and sets nodes to PENDING
        - ExecutePipelineFrameCommand executes PENDING nodes
        - ClosePipelineFrameCommand stops the pipeline if all nodes are done
    """
    ##############
    thing = TinyPipelineExample()
    thing.do_it()


# def _render_training_pipeline() -> None:
#     """
#     Just the inner portion of our pipeline:
#     - load training parameters
#     - load the data
#     - split data 80/20 for train/eval
#     - train model using 80% data and training parameters
#     - evaluate model using 20% data and trained model
#     """
#     di_container = Pipeline3DiContainer(args=tuple())
#     di_container._logging_client().configure_logging()
#
#     ##############
#
#     factory = PipelineBuilderFactory()
#     builder_components = factory.get_instance("demo-pipeline")
#
#     pipeline = builder_components.dag()
#     root = builder_components.namespace_client()
#
#     # SINGLE PIPELINE
#     pipeline.add_node(root.node("load-parameters"))
#     pipeline.add_node(root.node("load-data"))
#     pipeline.add_node(root.node("prepare-data"))
#     pipeline.add_node(root.node("train-model"))
#     pipeline.add_node(root.node("evaluate-model"))
#
#     pipeline.add_dependency(root.node("prepare-data"), root.node("load-data"))
#
#     pipeline.add_dependencies(root.node("train-model"), [
#         root.node("load-parameters"),
#         root.node("prepare-data"),
#     ])
#     pipeline.add_dependencies(root.node("evaluate-model"), [
#         root.node("train-model"),
#         root.node("prepare-data"),
#     ])
#
#     ###############
#
#     components = pipeline.build()
#
#     dot_dag = DotDag(
#         node_client=components.node_client(),
#         dependencies_client=components.node_dependencies_client(),
#         node_state_client=components.state_client(),
#     )
#     svg_client = DagSvg(dot_dag=dot_dag)
#     viz = DagVisualizer(svg_client=svg_client)
#     viz.execute()


# def _render_xval_training_pipeline() -> None:
#     """
#     The training pipeline from above, but using cross(5) fold validation
#     - load training parameters
#     - load the data
#     - split data 80/20 for train/eval
#     - train model using 80% data and training parameters
#     - evaluate model using 20% data and trained model
#     """
#     di_container = Pipeline3DiContainer(args=tuple())
#     di_container._logging_client().configure_logging()
#
#     ##############
#
#     factory = PipelineBuilderFactory()
#     builder_components = factory.get_instance()
#
#     pipeline = builder_components.dag()
#     root = builder_components.namespace_client()
#     multiplexer = builder_components.multiplex_client()
#
#     xval_ns = root.namespace("x-validation")
#     xval_fold = multiplexer.get_instance(xval_ns, range(5))
#
#     pipeline.add_nodes(xval_fold.nodes("load-parameters"))
#     pipeline.add_nodes(xval_fold.nodes("load-data"))
#     pipeline.add_nodes(xval_fold.nodes("prepare-data"))
#     pipeline.add_nodes(xval_fold.nodes("train-model"))
#     pipeline.add_nodes(xval_fold.nodes("evaluate-model"))
#     pipeline.add_node(xval_ns.node("average-results"))
#
#     xval_fold.add_internal_dependency("prepare-data", "load-data")
#
#     xval_fold.add_internal_dependencies("train-model", ["load-parameters", "prepare-data"])
#     xval_fold.add_internal_dependencies("evaluate-model", ["train-model", "prepare-data"])
#
#     pipeline.add_dependencies(xval_ns.node("average-results"), xval_fold.nodes("evaluate-model"))
#
#     ###############
#
#     components = pipeline.build()
#
#     dot_dag = DotDag(
#         node_client=components.node_client(),
#         dependencies_client=components.node_dependencies_client(),
#         node_state_client=components.state_client(),
#     )
#     svg_client = DagSvg(dot_dag=dot_dag)
#     viz = DagVisualizer(svg_client=svg_client)
#     viz.execute()


# def _render_xval_hpo_training_pipeline() -> None:
#     """
#     The training pipeline from above, but using HPO for the training parameters
#     - load training parameters
#     - load the data
#     - split data 80/20 for train/eval
#     - train model using 80% data and training parameters
#     - evaluate model using 20% data and trained model
#     """
#     di_container = Pipeline3DiContainer(args=tuple())
#     di_container._logging_client().configure_logging()
#
#     ##############
#
#     factory = PipelineBuilderFactory()
#     builder_components = factory.get_instance()
#
#     pipeline = builder_components.dag()
#     root = builder_components.namespace_client()
#     multiplexer = builder_components.multiplex_client()
#
#     hpo_ns = root.namespace("hpo")
#     hpo_fold = multiplexer.get_instance(hpo_ns, ["alpha", "beta"])
#
#     pipeline.add_node(hpo_ns.node("best-model"))
#
#     def xval_callback(n: PipelineNode) -> None:
#         xval_ns = hpo_ns.namespace(n.name)
#         xval_fold = multiplexer.get_instance(xval_ns, range(2))
#
#         pipeline.add_nodes(xval_fold.nodes("load-parameters"))
#         pipeline.add_nodes(xval_fold.nodes("load-data"))
#         pipeline.add_nodes(xval_fold.nodes("prepare-data"))
#         pipeline.add_nodes(xval_fold.nodes("train-model"))
#         pipeline.add_nodes(xval_fold.nodes("evaluate-model"))
#         pipeline.add_node(xval_ns.node("average-results"))
#
#         xval_fold.add_internal_dependency("prepare-data", "load-data")
#
#         xval_fold.add_internal_dependencies("train-model", ["load-parameters", "prepare-data"])
#         xval_fold.add_internal_dependencies("evaluate-model", ["train-model", "prepare-data"])
#
#         pipeline.add_dependencies(
#             xval_ns.node("average-results"),
#             xval_fold.nodes("evaluate-model"),
#         )
#
#         pipeline.add_dependency(hpo_ns.node("best-model"), xval_ns.node("average-results"))
#
#     hpo_fold.apply("xval", xval_callback)
#
#     ###############
#
#     components = pipeline.build()
#
#     dot_dag = DotDag(
#         node_client=components.node_client(),
#         dependencies_client=components.node_dependencies_client(),
#         node_state_client=components.state_client(),
#     )
#     svg_client = DagSvg(dot_dag=dot_dag)
#     viz = DagVisualizer(svg_client=svg_client)
#     viz.execute()


if __name__ == "__main__":
    # _render_training_pipeline()
    # _render_xval_training_pipeline()
    # _render_xval_hpo_training_pipeline()
    _render_tiny_pipeline()


# maybe pipeline.add_node("name", plugin)?
# IHandleNodes(Protocol)
#   @on_state_change()
#   def dependencies(self, node_client) -> None:
#     if condition:
#       node_client.prevent()
