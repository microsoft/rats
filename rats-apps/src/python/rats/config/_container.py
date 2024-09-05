from rats import apps
from ._configuration import IFactoryToFactoryWithConfig
from ._service_ids import Services


class ConfigFactoryContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @property
    def factory_to_factory_with_config(self) -> IFactoryToFactoryWithConfig:
        return self._app.get(Services.FACTORY_TO_FACTORY_WITH_CONFIG)
