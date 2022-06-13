from pathlib import Path

from oneml.lorenzo.pipelines import InMemoryStorage
from oneml.lorenzo.pipelines2._scratch_storage_example._output_client import MyPipelineOutput
from oneml.lorenzo.pipelines2._scratch_storage_example._samples import (
    LoadSamplesNodeProvider,
    Samples,
)
from oneml.lorenzo.pipelines2._scratch_storage_example._writers import (
    DictionaryWriter,
    LocalStorage,
    SimpleDataclassWriter,
    WriterRegistry,
)


def _main() -> None:
    """
    scratch/
        {pipeline-name}-{timestamp}/
            iteration-0/
                samples/
                    *.tsv

    scratch/
            samples/
                *.tsv
    """
    registry = WriterRegistry()

    dict_writer = DictionaryWriter(path=Path("./scratch/samples/samples.json"))
    simple_dataclass_writer = SimpleDataclassWriter(dict_writer=dict_writer)

    registry.register(dict, dict_writer)
    registry.register(Samples, simple_dataclass_writer)

    memory_storage = InMemoryStorage()
    local_storage = LocalStorage(writer_registry=registry)

    output_client = MyPipelineOutput(memory_storage=memory_storage, local_storage=local_storage)

    step_provider = LoadSamplesNodeProvider(output_client=output_client)
    step_provider.get_pipeline_node().execute_node()

    # registry = PipelineRegistry()
    #
    # dag_builder = PipelineNodeDagBuilder()
    # pipeline = MyPipelineProvider(dag_builder)
    #
    # # Plugins across the code can register pipeline "providers"
    # # Pipelines can only be registered once so first provider to register wins
    # registry.register(MyPipeline, pipeline)
    #
    # # A runner will query the registry and execute a pipeline
    # client = LocalPipelineClient(registry=registry)
    # client.execute(MyPipeline)


if __name__ == "__main__":
    _main()
