from rats import apps
from rats.app import RatsApp as LegacyApp

from . import ux
from ._interfaces import IPipelineRunnerFactory


class LegacyServicesWrapperContainer(apps.Container):
    @apps.autoid_service
    def legacy_app(self) -> LegacyApp:
        return LegacyApp.default()

    @apps.autoid_service
    def pipeline_runner_factory(self) -> IPipelineRunnerFactory:
        legacy_app = self.get(apps.autoid(self.legacy_app))
        return legacy_app.get_service(ux.RatsProcessorsUxServices.PIPELINE_RUNNER_FACTORY)


class Services:
    PIPELINE_RUNNER_FACTORY = apps.autoid(LegacyServicesWrapperContainer.pipeline_runner_factory)
