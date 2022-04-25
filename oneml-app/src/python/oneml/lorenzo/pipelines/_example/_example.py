from matplotlib import pyplot

from oneml.lorenzo.pipelines import InMemoryStorage, TypeNamespaceClient
from oneml.lorenzo.pipelines._example._pipeline import ExamplePipeline


def _run_example() -> None:
    storage = InMemoryStorage()
    namespace_client = TypeNamespaceClient()

    pipeline = ExamplePipeline(
        storage=storage,
        namespace_client=namespace_client,
    )
    pipeline.execute()

    pyplot.show()

    for k, v in storage._data.items():
        print(k)


if __name__ == "__main__":
    _run_example()
