import logging

from immunodata.immunocli.next import BasicCliPlugin

from ..services import OnemlHabitatsServices
from ..services._locate_habitats_cli_di_container import LocateHabitatsCliDiContainers
from ._di_container import OnemlHabitatsDiContainer

logger = logging.getLogger(__name__)


class OnemlHabitatsCliPlugin(BasicCliPlugin[None]):
    _container: OnemlHabitatsDiContainer

    def __post_init__(self) -> None:
        self._container = OnemlHabitatsDiContainer(app=self.app)

        self.app.register_container(OnemlHabitatsDiContainer, self._container)
