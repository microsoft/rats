from typing import Any

from rats import apps


@apps.autoscope
class ExampleServices:
    FOO = apps.ServiceId[Any]("foo")
    GOO = apps.ServiceId[Any]("goo")
    ZOO = apps.ServiceId[Any]("zoo")


class ExampleContainer:
    @apps.service(ExampleServices.FOO)
    def moo(self) -> Any:
        return "foo"

    @apps.autoid_service
    def bar(self) -> Any:
        return "bar"

    @apps.service(ExampleServices.GOO)
    @apps.service(ExampleServices.ZOO)
    def zoo(self) -> Any:
        return "zoo"


class TestServiceIds:
    def test_explicit_id(self) -> None:
        method = ExampleContainer.moo
        expected = ExampleServices.FOO
        found = apps.get_method_service_id(method)
        assert found == expected

    def test_auto_id(self) -> None:
        method = ExampleContainer.bar
        expected = apps.ServiceId[Any]("rats_test.apps.test_service_ids:ExampleContainer[bar]")
        found = apps.get_method_service_id(method)
        assert found == expected

    def test_multiple_ids(self) -> None:
        method = ExampleContainer.zoo
        expected = set((ExampleServices.GOO, ExampleServices.ZOO))
        found_all = set(apps.get_method_service_ids(method))
        assert found_all == expected
        found = apps.get_method_service_id(method)
        assert found in expected
