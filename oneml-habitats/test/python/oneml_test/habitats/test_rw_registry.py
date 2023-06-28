import numpy as np
import pandas as pd

from oneml.habitats.io import OnemlHabitatsIoServices
from oneml.io import OnemlIoServices
from oneml.processors.io import IGetReadServicesForType, IGetWriteServicesForType


def test_registered_rw_str(
    get_read_services_for_type: IGetReadServicesForType,
    get_write_services_for_type: IGetWriteServicesForType,
) -> None:
    read_services = get_read_services_for_type.get_read_service_ids(str)
    assert read_services == {
        "memory": OnemlIoServices.INMEMORY_READER,
        "file": OnemlIoServices.PICKLE_LOCAL_READER,
    }

    write_services = get_write_services_for_type.get_write_service_ids(str)
    assert write_services == {
        "memory": OnemlIoServices.INMEMORY_WRITER,
        "file": OnemlIoServices.PICKLE_LOCAL_WRITER,
    }


def test_registered_rw_np(
    get_read_services_for_type: IGetReadServicesForType,
    get_write_services_for_type: IGetWriteServicesForType,
) -> None:
    read_services = get_read_services_for_type.get_read_service_ids(np.ndarray)
    assert read_services == {
        "memory": OnemlIoServices.INMEMORY_READER,
        "file": OnemlHabitatsIoServices.NUMPY_LOCAL_READER,
    }

    write_services = get_write_services_for_type.get_write_service_ids(np.ndarray)
    assert write_services == {
        "memory": OnemlIoServices.INMEMORY_WRITER,
        "file": OnemlHabitatsIoServices.NUMPY_LOCAL_WRITER,
    }


def test_registered_rw_pd(
    get_read_services_for_type: IGetReadServicesForType,
    get_write_services_for_type: IGetWriteServicesForType,
) -> None:
    read_services = get_read_services_for_type.get_read_service_ids(pd.DataFrame)
    assert read_services == {
        "memory": OnemlIoServices.INMEMORY_READER,
        "file": OnemlHabitatsIoServices.PANDAS_LOCAL_READER,
    }

    write_services = get_write_services_for_type.get_write_service_ids(pd.DataFrame)
    assert write_services == {
        "memory": OnemlIoServices.INMEMORY_WRITER,
        "file": OnemlHabitatsIoServices.PANDAS_LOCAL_WRITER,
    }
