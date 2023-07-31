import logging

from oneml.app import OnemlAppServices
from oneml.io import OnemlIoServices
from oneml.services import (
    IExecutable,
    IProvideServices,
    after,
    before,
    executable,
    service_group,
    service_provider,
)

from ._pipeline import HelloWorldPipeline, OnemlExamplePipelines

logger = logging.getLogger(__name__)


class OnemlExamplesDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlExamplePipelines.HELLO_WORLD)
    def hello_world_pipeline(self) -> HelloWorldPipeline:
        return HelloWorldPipeline(
            builder_client=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER),
            output_client=self._app.get_service(OnemlIoServices.NODE_OUTPUT_CLIENT),
        )

    @service_group(before(OnemlExamplePipelines.HELLO_WORLD))
    def before_pipeline(self) -> IExecutable:
        return executable(lambda: print("hook called before() execution of hello world pipeline"))

    @service_group(after(OnemlExamplePipelines.HELLO_WORLD))
    def after_pipeline(self) -> IExecutable:
        return executable(lambda: print("hook called after() execution of hello world pipeline"))
