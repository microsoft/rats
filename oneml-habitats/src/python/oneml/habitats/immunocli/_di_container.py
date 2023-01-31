from functools import lru_cache
from pathlib import Path

from immunodata.cli import DiContainerSearch, DiContainerSearchFactory, ILocateDiContainers
from immunodata.core._immunocli import PoetryComponentResourcesPath
from immunodata.core.config.immunoproject import ImmunoProjectConfig
from immunodata.immunocli.next import ImmunocliContainer
from immunodata.resources import ImmunodataResourceLocator

from oneml import habitats


class OnemlHabitatsDiContainer:

    _app: ILocateDiContainers

    def __init__(self, app: ILocateDiContainers):
        self._app = app

    @lru_cache()
    def resources_locator(self) -> ImmunodataResourceLocator:
        return ImmunodataResourceLocator(
            base_path=self._app_resources_path().get_root_path(),
        )

    @lru_cache()
    def _app_resources_path(self) -> PoetryComponentResourcesPath:
        return PoetryComponentResourcesPath(
            project_config=self._project_config(),
            module_path=Path(habitats.__path__[0]),
            component_name="oneml-habitats",
        )

    @lru_cache
    def container_search(self) -> DiContainerSearch:
        return self._di_container_search_factory().get_instance(self)

    def _di_container_search_factory(self) -> DiContainerSearchFactory:
        return self._cli_container().di_container_search_factory()

    def _project_config(self) -> ImmunoProjectConfig:
        return self._cli_container().project_config()

    def _cli_container(self) -> ImmunocliContainer:
        return self._app.find_container(ImmunocliContainer)
