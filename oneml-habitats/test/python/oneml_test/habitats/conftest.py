import logging

import pytest

from oneml.app import OnemlApp
from oneml.processors.io import IGetReadServicesForType, IGetWriteServicesForType
from oneml.processors.services import OnemlProcessorsServices

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def app() -> OnemlApp:
    app = OnemlApp.default()
    return app


@pytest.fixture(scope="package")
def get_read_services_for_type(app: OnemlApp) -> IGetReadServicesForType:
    return app.get_service(OnemlProcessorsServices.GET_TYPE_READER)


@pytest.fixture(scope="package")
def get_write_services_for_type(app: OnemlApp) -> IGetWriteServicesForType:
    return app.get_service(OnemlProcessorsServices.GET_TYPE_WRITER)
