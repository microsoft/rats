from oneml.services import ServiceFactory, TypedServiceContainer

from ._examples import CatService, ExampleServiceGroups, make_cat


class TestTypedServiceContainer:
    _container: TypedServiceContainer[CatService]

    def setup_method(self) -> None:
        factory = ServiceFactory()
        factory.add_service(ExampleServiceGroups.CAT, make_cat)
        factory.add_group(ExampleServiceGroups.CAT, make_cat)
        self._container = TypedServiceContainer[CatService](factory)

    def test_basics(self) -> None:
        cat = self._container.get_service("cat")
        assert cat.speak() == "meow"
        cats = list(self._container.get_service_group("cat"))

        assert len(cats) > 0
        for c in cats:
            assert c.speak() == "meow"
