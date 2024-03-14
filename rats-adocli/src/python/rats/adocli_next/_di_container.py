from rats.adocli_next._pipelines import AdocliPipelinesClient
from rats.app import RatsAppServices
from rats.app._rats_app_services import RatsAppGroups
from rats.services import IProvideServices, ServiceId, group, provider, scoped_service_ids


class ExampleService:
    def create_user(self) -> None:
        print("created user")


@scoped_service_ids
class RatsAdocliServices:
    EXAMPLE_CLIENT = ServiceId[ExampleService]("example-client")


class RatsAdocliDiContainer:
    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @provider(RatsAdocliServices.EXAMPLE_CLIENT)
    def example_client(self) -> ExampleService:
        return ExampleService()

    @group(RatsAppGroups.PIPELINE_CONTAINER)
    def pipelines_client(self) -> AdocliPipelinesClient:
        return AdocliPipelinesClient(
            builder_client=self._app.get_service(RatsAppServices.PIPELINE_BUILDER)
        )
