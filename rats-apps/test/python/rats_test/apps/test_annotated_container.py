from collections.abc import Callable
from typing import Any, NamedTuple, ParamSpec, TypeVar

import pytest

from rats import apps
from rats.apps._categories import ProviderCategories


class ExampleStorage:

    called: int
    data: list[str]

    def __init__(self) -> None:
        self.called = 0
        self.data = []

    def save(self, data: str) -> None:
        self.called += 1
        self.data.append(data)


class ExampleConfig(NamedTuple):
    account: str
    table: str
    max: int


class ExampleExecutable:

    called: int

    def __init__(self) -> None:
        self.called = 0

    def execute(self) -> None:
        self.called += 1


P_ProviderParams = ParamSpec("P_ProviderParams")


def custom(callback: Callable[[P_ProviderParams], apps.ServiceId]) -> Callable[[P_ProviderParams], apps.ServiceId]:
    def run(*args, **kwargs) -> apps.ServiceId:
        return callback(*args, **kwargs)

    return run


class ExampleGroups:
    STORAGE_REPLICAS = apps.ServiceId[ExampleStorage]("/group/storage-replicas")
    EXECUTABLES = apps.ServiceId[ExampleExecutable]("/group/exe")
    MISSING = apps.ServiceId[ExampleStorage]("/group/missing")


class ExampleIds:
    STORAGE = apps.ServiceId[ExampleStorage]("/service/storage")
    EXECUTABLE = apps.ServiceId[ExampleExecutable]("/service/exe")
    MISSING = apps.ServiceId[Any]("/service/missing")
    DUPLICATE = apps.ServiceId[Any]("/service/duplicate")
    GROUPS = ExampleGroups

    make_service_id = custom(lambda x: apps.ServiceId[Any](f"/generated/{x}"))
    make_config_id = custom(lambda x: apps.ConfigId[Any](f"/generated/config-{x}"))


class ExampleContainer(apps.AnnotatedContainer):

    @apps.service(ExampleIds.STORAGE)
    def storage(self) -> ExampleStorage:
        return ExampleStorage()

    @apps.service(ExampleIds.DUPLICATE)
    def duplicate_1(self) -> ExampleStorage:
        return ExampleStorage()

    @apps.service(ExampleIds.DUPLICATE)
    def duplicate_2(self) -> ExampleStorage:
        return ExampleStorage()

    @apps.group(ExampleIds.GROUPS.STORAGE_REPLICAS)
    def replica_1(self) -> ExampleStorage:
        return ExampleStorage()

    @apps.group(ExampleIds.GROUPS.STORAGE_REPLICAS)
    def replica_2(self) -> ExampleStorage:
        return ExampleStorage()

    @apps.container()
    def plugin(self) -> apps.Container:
        return ExamplePlugin(self)


class ExamplePlugin(apps.AnnotatedContainer):

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.fallback_service(ExampleIds.EXECUTABLE)
    def default_exe(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.service(ExampleIds.make_service_id("foo"))
    def foo(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.fallback_service(ExampleIds.make_service_id("foo"))
    def fallback_foo(self) -> ExampleExecutable:
        raise NotImplementedError("this fallback should never run")

    @apps.fallback_group(ExampleIds.make_service_id("foo-group.hit-fallback"))
    def fallback_foo_1(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.fallback_group(ExampleIds.make_service_id("foo-group.hit-fallback"))
    def fallback_foo_2(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.group(ExampleIds.make_service_id("foo-group.miss-fallback"))
    def fallback_foo_hit(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.fallback_group(ExampleIds.make_service_id("foo-group.miss-fallback"))
    def fallback_foo_3(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.fallback_group(ExampleIds.make_service_id("foo-group.miss-fallback"))
    def fallback_foo_4(self) -> ExampleExecutable:
        return ExampleExecutable()

    @apps.fallback_config(ExampleIds.make_config_id("foo-config.hit-fallback"))
    def fallback_foo_config(self) -> ExampleConfig:
        return ExampleConfig(
            account="foo-fallback",
            table="bar",
            max=100,
        )

    @apps.config(ExampleIds.make_config_id("foo-config.miss-fallback"))
    def foo_config(self) -> ExampleConfig:
        return ExampleConfig(
            account="foo-miss",
            table="bar",
            max=100,
        )

    @apps.fallback_config(ExampleIds.make_config_id("foo-config.miss-fallback"))
    def fallback_foo_config_miss(self) -> ExampleConfig:
        return ExampleConfig(
            account="foo-miss-fallback",
            table="bar",
            max=100,
        )

    @apps.config(ExampleIds.make_config_id("foo-config.duplicate"))
    def foo_config_duplicate_1(self) -> ExampleConfig:
        return ExampleConfig(
            account="foo-hit",
            table="bar",
            max=100,
        )

    @apps.config(ExampleIds.make_config_id("foo-config.duplicate"))
    def foo_config_duplicate_2(self) -> ExampleConfig:
        return ExampleConfig(
            account="foo-hit",
            table="bar",
            max=100,
        )


class TestAnnotatedContainer:
    _app: ExampleContainer

    def setup_method(self) -> None:
        self._app = ExampleContainer()

    def test_services_api(self) -> None:
        """
        Basic API for retrieving services from annotated containers.

        - you get a service by providing a ServiceId
        - the ServiceId generic holds the type returned by .get()
        - multiple calls to .get() return the same instance of a given ServiceId
        - method verifies that exactly one service matches a given ServiceId
        - if the service id is not found, we look for and return a fallback service
        - if the fallback service is not found, we raise a ServiceNotFoundError
        - the fallback service is ignored if the main service is found
        - there must still be at most one match for the service within the fallback id
        """
        storage = self._app.get(ExampleIds.STORAGE)
        assert storage.called == 0
        storage.save("hello")
        assert storage.called == 1

        storage_2 = self._app.get(ExampleIds.STORAGE)
        assert storage == storage_2
        assert storage.called == storage_2.called

        with pytest.raises(apps.ServiceNotFoundError):
            self._app.get(ExampleIds.MISSING)

        with pytest.raises(apps.DuplicateServiceError):
            self._app.get(ExampleIds.DUPLICATE)

        fallback = self._app.get(ExampleIds.EXECUTABLE)
        fallback.execute()
        assert fallback.called == 1

        foo = self._app.get(ExampleIds.make_service_id("foo"))
        foo.execute()
        assert foo.called == 1

    def test_config_api(self) -> None:
        """
        Basic API for retrieving configs from annotated containers.

        - you get a config by providing a ConfigId
        - the ConfigId generic holds the type returned by .get_config()
        - configs are bound to NamedTuple types and should strictly be data structures
        - configs should be immutable and should not have side effects
        - multiple calls to .get_config() return the same instance
        - method verifies that exactly one config matches a given ConfigId
        - if the config id is not found, we look for and return a fallback config
        - if the fallback config is not found, we raise a ServiceNotFoundError
        - the fallback config is ignored if the main config is found
        - there must still be at most one match for the config within the fallback id
        """
        foo = self._app.get_config(ExampleIds.make_config_id("foo-config.hit-fallback"))
        assert foo.account == "foo-fallback"

        foo_2 = self._app.get_config(ExampleIds.make_config_id("foo-config.hit-fallback"))
        assert foo == foo_2

        with pytest.raises(apps.ServiceNotFoundError):
            self._app.get_config(ExampleIds.make_config_id("missing-thing"))

        with pytest.raises(apps.DuplicateServiceError):
            self._app.get_config(ExampleIds.make_config_id("foo-config.duplicate"))

        foo = self._app.get_config(ExampleIds.make_config_id("foo-config.miss-fallback"))
        assert foo.account == "foo-miss"

    def test_groups_api(self) -> None:
        """
        Basic API for retrieving groups of services from annotated containers.

        - you get a group by providing a ServiceId
        - the ServiceId generic holds the list type returned by .get_group()
        - multiple calls to .get_group() return the same instances of a given ServiceId
        - method can return zero or more results
        - if the group is empty, the matching fallback group is returned
        - if the group is not empty, the fallback group is not included in the results
        """
        # just casting to make assertions easier
        replicas = list(self._app.get_group(ExampleIds.GROUPS.STORAGE_REPLICAS))

        for storage in replicas:
            storage.save("hello")
            assert storage.called == 1

        for s2 in self._app.get_group(ExampleIds.GROUPS.STORAGE_REPLICAS):
            assert s2.called == 1

        assert len(replicas) == 2

        missing = self._app.get_group(ExampleIds.GROUPS.MISSING)
        assert len(list(missing)) == 0

        for fallback in self._app.get_group(ExampleIds.make_service_id("foo-group.hit-fallback")):
            fallback.execute()
            assert fallback.called == 1

        assert len(list(self._app.get_group(ExampleIds.make_service_id("foo-group.hit-fallback")))) == 2
        assert len(list(self._app.get_group(ExampleIds.make_service_id("foo-group.miss-fallback")))) == 1

    def test_has_apis(self) -> None:
        assert self._app.has(ExampleIds.STORAGE)
        assert self._app.has_group(ExampleIds.GROUPS.STORAGE_REPLICAS)
        assert self._app.has_config(ExampleIds.make_config_id("foo-config.miss-fallback"))
        assert self._app.has_category(ProviderCategories.SERVICE, ExampleIds.STORAGE)

        assert not self._app.has(ExampleIds.MISSING)
        assert not self._app.has_group(ExampleIds.GROUPS.MISSING)
        assert not self._app.has_config(ExampleIds.make_config_id("foo-config.missing"))
        assert not self._app.has_category(ProviderCategories.SERVICE, ExampleIds.MISSING)
