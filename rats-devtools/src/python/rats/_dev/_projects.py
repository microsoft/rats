from rats import apps


class ProjectPluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app
