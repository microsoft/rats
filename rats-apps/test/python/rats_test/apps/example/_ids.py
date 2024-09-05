from rats import apps

from ._storage import StorageClient, StorageSettings


@apps.autoscope
class ExampleStorageConfigIds:
    # a couple example config ids for different storage accounts
    STORAGE = apps.ServiceId[StorageSettings]("storage")
    OTHER_STORAGE = apps.ServiceId[StorageSettings]("other-storage")
    RANDOM_STORAGE = apps.ServiceId[StorageSettings]("random-storage")
    DUPLICATE = apps.ServiceId[StorageSettings]("DUPLICATE")


@apps.autoscope
class ExampleGroupIds:
    STORAGE = apps.ServiceId[StorageClient]("storage")
    OTHER_STORAGE = apps.ServiceId[StorageClient]("other-storage")


@apps.autoscope
class ExampleIds:
    # a couple example storage clients for different destinations
    STORAGE = apps.ServiceId[StorageClient]("default-storage")
    OTHER_STORAGE = apps.ServiceId[StorageClient]("other-storage")

    DUPLICATE_SERVICE = apps.ServiceId[StorageClient]("duplicate-service")

    CONFIGS = ExampleStorageConfigIds
    GROUPS = ExampleGroupIds
