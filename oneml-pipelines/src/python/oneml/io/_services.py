from typing import Any

from oneml.services import ServiceId, scoped_service_ids

from ._io_data import IFormatUri, IGetLoaders, IGetPublishers
from ._rw_data import IReadAndWriteData, IReadData, IWriteData


@scoped_service_ids
class OnemlIoServices:
    PIPELINE_LOADERS_GETTER = ServiceId[IGetLoaders[Any]]("pipeline-loaders-getter")
    PIPELINE_PUBLISHERS_GETTER = ServiceId[IGetPublishers[Any]]("pipeline-publishers-getter")

    INMEMORY_URI_FORMATTER = ServiceId[IFormatUri[Any]]("inmemory-uri-formatter")
    FILESYSTEM_URI_FORMATTER = ServiceId[IFormatUri[Any]]("filesystem-uri-formatter")

    # These are split so users can request a specific interface, but we resolve them to the same id
    # We can easily change ID and split these up if our di container needs to use them differently
    INMEMORY_READER = ServiceId[IReadData[Any]]("inmemory-rw")
    INMEMORY_WRITER = ServiceId[IWriteData[Any]]("inmemory-rw")
    INMEMORY_RW = ServiceId[IReadAndWriteData[Any]]("inmemory-rw")
    PICKLE_LOCAL_READER = ServiceId[IReadData[object]]("pickle-local-rw")
    PICKLE_LOCAL_WRITER = ServiceId[IWriteData[object]]("pickle-local-rw")
    PICKLE_LOCAL_RW = ServiceId[IReadAndWriteData[object]]("pickle-local-rw")
