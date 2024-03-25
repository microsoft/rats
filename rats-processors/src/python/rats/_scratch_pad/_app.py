from oneml.services import IExecutable, ServiceId

from ._ids import RatsAppServices
from ._pipeline import Example3PipelineContainer
from ._v2 import (
    App,
    ServiceContainer,
    container_group,
    service_provider,
)


class RatsCli(IExecutable):
    def execute(self) -> None:
        print("hello, world")


class RatsAppContainer(ServiceContainer):
    @service_provider(RatsAppServices.CLI)
    def cli(self) -> App:
        return self.get_service(ServiceId[App]("draw-pipeline"))

    @container_group()
    def example_pipeline_plugin(self) -> Example3PipelineContainer:
        return Example3PipelineContainer(self)


def run() -> None:
    container = RatsAppContainer()
    container.get_service(RatsAppServices.CLI).execute()
