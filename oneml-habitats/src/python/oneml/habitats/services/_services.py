from pathlib import Path

from immunodata.blob import IBlobClientFactory

from oneml.services import ServiceId, scoped_service_ids

from ._locate_habitats_cli_di_container import ILocateHabitatsCliDiContainer
from ._register_rw import OnemlHabitatsRegisterReadersAndWriters


@scoped_service_ids
class OnemlHabitatsServices:
    BLOB_CLIENT_FACTORY = ServiceId[IBlobClientFactory]("blob-client-factory")
    LOCATE_HABITATS_CLI_DI_CONTAINERS = ServiceId[ILocateHabitatsCliDiContainer](
        "locate-habitats-cli-di-containers"
    )
    TMP_PATH = ServiceId[Path]("tmp-path")
    PLUGIN_REGISTER_READERS_AND_WRITERS = ServiceId[OnemlHabitatsRegisterReadersAndWriters](
        "plugin-register-readers-and-writers",
    )
    BLOB_CACHE_PATH = ServiceId[Path]("blob-cache-path")
