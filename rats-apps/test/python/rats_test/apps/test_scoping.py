from typing import Any

from rats import apps


@apps.autoscope
class ExampleServices:
    FOO = apps.ServiceId[Any]("foo")
    CONFIG = apps.ServiceId[Any]("config")
    OTHER = 52

    @staticmethod
    def bar(name: str) -> apps.ServiceId[Any]:
        return apps.ServiceId[Any](name)

    @staticmethod
    def custom(name: str) -> str:
        return f"prefix[{name}]"


class TestScoping:
    def test_properties_are_scoped(self) -> None:
        expected = f"{__name__}:ExampleServices[foo]"
        assert ExampleServices.FOO.name == expected

    def test_configs_are_scoped(self) -> None:
        expected = f"{__name__}:ExampleServices[config]"
        assert ExampleServices.CONFIG.name == expected

    def test_functions_are_scoped(self) -> None:
        expected = f"{__name__}:ExampleServices[bar]"
        assert ExampleServices.bar("bar").name == expected

    def test_non_scoped_properties(self) -> None:
        assert ExampleServices.OTHER == 52

    def test_non_scoped_functions(self) -> None:
        assert ExampleServices.custom("foo") == "prefix[foo]"
