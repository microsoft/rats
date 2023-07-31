from oneml.services import IProvideServices, before, service_group, service_provider

from ._search_command import AzClient, AzLoginCommand, OpenAiRunner, SearchCommand, SearchServices


class SearchDiContainer:
    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(SearchServices.MAIN)
    def search_command(self) -> SearchCommand:
        return SearchCommand(openai=self._app.get_service(SearchServices.OPENAI))

    @service_group(before(SearchServices.MAIN))
    def az_login_command(self) -> AzLoginCommand:
        return AzLoginCommand(AzClient())

    @service_provider(SearchServices.OPENAI)
    def openai(self) -> OpenAiRunner:
        return OpenAiRunner()
