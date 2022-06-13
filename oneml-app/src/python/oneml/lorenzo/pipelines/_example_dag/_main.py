from oneml.lorenzo.pipelines._example_dag._pipeline import ExamplePipeline2


def _run() -> None:
    pipeline = ExamplePipeline2()
    pipeline.main()


if __name__ == "__main__":
    _run()
