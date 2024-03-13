from typing import Any

from rats.services import IExecutable, ServiceId, scoped_service_ids

from ._io_data import IFormatUri, IManageLoaders, IManagePublishers
from ._node_output import NodeOutputClient
from ._rw_data import IReadAndWriteData, IReadData, IWriteData


@scoped_service_ids
class RatsIoServices:
    REGISTRY_PLUGINS = ServiceId[IExecutable]("io-registry-plugins")

    NODE_OUTPUT_CLIENT = ServiceId[NodeOutputClient]("node-output-client")
    PIPELINE_LOADERS_GETTER = ServiceId[IManageLoaders[Any]]("pipeline-loaders-getter")
    PIPELINE_PUBLISHERS_GETTER = ServiceId[IManagePublishers[Any]]("pipeline-publishers-getter")

    INMEMORY_URI_FORMATTER = ServiceId[IFormatUri[Any]]("inmemory-uri-formatter")
    FILESYSTEM_URI_FORMATTER = ServiceId[IFormatUri[Any]]("filesystem-uri-formatter")

    # These are split so users can request a specific interface, but we resolve them to the same id
    # We can easily change ID and split these up if our di container needs to use them differently
    INMEMORY_READER = ServiceId[IReadData[Any]]("inmemory-rw")
    INMEMORY_WRITER = ServiceId[IWriteData[Any]]("inmemory-rw")
    INMEMORY_RW = ServiceId[IReadAndWriteData[Any]]("inmemory-rw")
    DILL_LOCAL_READER = ServiceId[IReadData[object]]("dill-local-rw")
    DILL_LOCAL_WRITER = ServiceId[IWriteData[object]]("dill-local-rw")
    DILL_LOCAL_RW = ServiceId[IReadAndWriteData[object]]("dill-local-rw")
    JSON_LOCAL_READER = ServiceId[IReadData[object]]("json-local-rw")
    JSON_LOCAL_WRITER = ServiceId[IWriteData[object]]("json-local-rw")
    JSON_LOCAL_RW = ServiceId[IReadAndWriteData[object]]("json-local-rw")
