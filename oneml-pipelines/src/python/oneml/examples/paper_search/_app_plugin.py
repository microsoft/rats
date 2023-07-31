from oneml.app_api import AppPlugin
from oneml.examples.paper_search._di_container import SearchDiContainer
from oneml.services import IManageServices


class OnemlPaperSearchPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(SearchDiContainer(app))
