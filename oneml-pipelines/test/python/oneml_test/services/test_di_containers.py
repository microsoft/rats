from oneml.services import ServiceFactory, service_group, service_provider

from ._examples import CatService, ExampleServiceGroups, ExampleServices, make_cat


class ExampleDiContainer:
    @service_provider(ExampleServices.CAT_1)
    def cat_1(self) -> CatService:
        return make_cat()

    @service_group(ExampleServiceGroups.CAT)
    def cat(self) -> CatService:
        return make_cat()


class TestContainerClient:
    def test_basics(self) -> None:
        factory = ServiceFactory()
        factory.parse_service_container(ExampleDiContainer())

        cat = factory.get_service(ExampleServices.CAT_1)
        assert cat.speak() == "meow"

        cats = list(factory.get_service_group(ExampleServiceGroups.CAT))
        assert len(cats) > 0
        for c in cats:
            assert c.speak() == "meow"
