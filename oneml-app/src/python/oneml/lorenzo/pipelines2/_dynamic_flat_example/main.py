from oneml.lorenzo.pipelines2 import LocalPipelineClient, PipelineNodeDagBuilder, PipelineRegistry
from oneml.lorenzo.pipelines2._dynamic_flat_example._pipeline import MyPipeline, MyPipelineProvider

# class MyPipeline(
#         IPipeline,
#         IProvidePipelines['MyPipeline'],
#         IPipelineNode,
#         IProvidePipelineNodes['MyPipeline']):
#
#     _registry: DagRegistry
#
#     def __init__(self):
#         builder = DagRegistryBuilder()
#         """
#         - You can register edges to nodes that are represented by extenal datasets.
#         - A provider of a node handles internal/external differences.
#         """
#         node_1 = type("MyPipeline-1", (MyPipeline,), {})
#         node_2 = type("MyPipeline-2", (MyPipeline,), {})
#         node_3 = type("MyPipeline-3", (MyPipeline,), {})
#         node_4 = type("MyPipeline-4", (MyPipeline,), {})
#         node_5 = type("MyPipeline-5", (MyPipeline,), {})
#
#         builder.register_node(node_1, self)  # type: ignore
#         builder.register_node(node_2, self)  # type: ignore
#         builder.register_node(node_3, self)  # type: ignore
#         builder.register_node(node_4, self)  # type: ignore
#         builder.register_node(node_5, self)  # type: ignore
#
#         builder.register_edges(node_2, tuple([node_3]))  # type: ignore
#         builder.register_edges(node_1, tuple([node_3, node_4]))  # type: ignore
#
#         self._registry = builder.build()
#
#     def get_pipeline(self) -> PipelineType:
#         return self
#
#     def execute_pipeline(self) -> None:
#         print("EXECUTE PIPELINE")
#         for x in self._registry.get_items():
#             x.get_pipeline_node().execute_node()
#
#     def get_pipeline_node(self) -> PipelineNodeType:
#         return self
#
#     def execute_node(self) -> None:
#         print("EXECUTE NODE")


def _main() -> None:
    registry = PipelineRegistry()

    dag_builder = PipelineNodeDagBuilder()
    pipeline = MyPipelineProvider(dag_builder)

    # Plugins across the code can register pipeline "providers"
    # Pipelines can only be registered once so first provider to register wins
    registry.register(MyPipeline, pipeline)

    # A runner will query the registry and execute a pipeline
    client = LocalPipelineClient(registry=registry)
    client.execute(MyPipeline)


if __name__ == "__main__":
    _main()
