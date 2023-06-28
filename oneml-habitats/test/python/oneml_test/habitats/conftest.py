import logging
import shutil
from pathlib import Path
from typing import Any, Iterator

import pytest

from oneml.app import OnemlApp
from oneml.processors import OnemlProcessorsServices
from oneml.processors.io import IGetReadServicesForType, IGetWriteServicesForType

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
