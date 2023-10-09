from functools import lru_cache

from immunodata.cli import ILocateDiContainers

from oneml.app import OnemlApp

from ._app_plugin import OnemlHabitatsImmunocliServices
from ._locate_habitats_cli_di_container import LocateHabitatsCliDiContainers


class OnemlHabitatsCliDiContainer:
    _app: ILocateDiContainers

    def __init__(self, app: ILocateDiContainers) -> None:
        self._app = app

    @lru_cache
    def oneml_app(self) -> OnemlApp:
        oneml_app = OnemlApp.default()
        oneml_app.add_service(
            OnemlHabitatsImmunocliServices.LOCATE_HABITATS_CLI_DI_CONTAINERS,
            lambda: LocateHabitatsCliDiContainers(self._app),
        )
        return oneml_app
