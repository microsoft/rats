from rats import apps

from ._storage import StorageClient, StorageSettings


@apps.autoscope
class ExampleConfigIds:
    # a couple example config ids for different storage accounts
    STORAGE = apps.ConfigId[StorageSettings]("storage")
    OTHER_STORAGE = apps.ConfigId[StorageSettings]("other-storage")
    RANDOM_STORAGE = apps.ConfigId[StorageSettings]("random-storage")
    DUPLICATE = apps.ConfigId[StorageSettings]("DUPLICATE")


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

    CONFIGS = ExampleConfigIds
    GROUPS = ExampleGroupIds
