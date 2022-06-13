from oneml.lorenzo.pipelines3._example._di_container import Pipeline3DiContainer


def _main() -> None:
    di_container = Pipeline3DiContainer(args=tuple())
    application = di_container.application()
    application.execute()

    # Simple Example Code
    # session = PipelineSession(NullPipeline())
    # pipeline_config = MlPipelineConfig(
    #     session_provider=lambda: session,
    #     executables_provider=lambda: {PipelineNode("pause-1"): lambda: PauseStep(1)},
    #     dependencies_provider=lambda: {},
    # )
    # pipeline_provider = MlPipelineProvider(pipeline_config)
    # session.set_pipeline(pipeline_provider.get_pipeline())
    # session.run_pipeline()


if __name__ == "__main__":
    _main()
