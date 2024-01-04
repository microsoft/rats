import logging

import pytest

from oneml.app import OnemlApp
from oneml.processors.io import (
    IGetReadServicesForType,
    IGetWriteServicesForType,
    OnemlProcessorsIoServices,
)
from oneml.processors.ux import OnemlProcessorsUxServices, PipelineRunnerFactory

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def app() -> OnemlApp:
    app = OnemlApp.default()
    return app


@pytest.fixture(scope="package")
def get_read_services_for_type(app: OnemlApp) -> IGetReadServicesForType:
    return app.get_service(OnemlProcessorsIoServices.GET_TYPE_READER)


@pytest.fixture(scope="package")
def get_write_services_for_type(app: OnemlApp) -> IGetWriteServicesForType:
    return app.get_service(OnemlProcessorsIoServices.GET_TYPE_WRITER)


@pytest.fixture(scope="package")
def pipeline_runner_factory(
    app: OnemlApp,
) -> PipelineRunnerFactory:
    return app.get_service(OnemlProcessorsUxServices.PIPELINE_RUNNER_FACTORY)
