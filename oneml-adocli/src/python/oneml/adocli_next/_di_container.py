from oneml.adocli_next._pipelines import AdocliPipelinesClient
from oneml.app import OnemlAppServices
from oneml.app._oneml_app_services import OnemlAppGroups
from oneml.services import IProvideServices, ServiceId, group, provider, scoped_service_ids


class ExampleService:

    def create_user(self) -> None:
        print("created user")


@scoped_service_ids
class OnemlAdocliServices:
    EXAMPLE_CLIENT = ServiceId[ExampleService]("example-client")


class OnemlAdocliDiContainer:

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @provider(OnemlAdocliServices.EXAMPLE_CLIENT)
    def example_client(self) -> ExampleService:
        return ExampleService()

    @group(OnemlAppGroups.PIPELINE_CONTAINER)
    def pipelines_client(self) -> AdocliPipelinesClient:
        return AdocliPipelinesClient(
            builder_client=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER)
        )
