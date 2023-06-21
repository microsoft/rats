import logging

from immunodata.immunocli.next import BasicCliPlugin

from ._di_container import OnemlHabitatsCliDiContainer

logger = logging.getLogger(__name__)


class OnemlHabitatsCliPlugin(BasicCliPlugin[None]):
    _container: OnemlHabitatsCliDiContainer

    def __post_init__(self) -> None:
        self._container = OnemlHabitatsCliDiContainer(app=self.app)

        self.app.register_container(OnemlHabitatsCliDiContainer, self._container)
