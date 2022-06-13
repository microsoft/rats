from oneml.lorenzo.cli import execute_command
from oneml.lorenzo.pipelines2 import LocalPipelineClient, PipelineNodeDagBuilder, PipelineRegistry


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
