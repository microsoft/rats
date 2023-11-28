from typing import NamedTuple

from oneml.services import ContextualServiceContainer, ServiceContainer, ServiceFactory

from ._examples import ExampleServiceGroups, ExampleServices, make_cat, make_russian_blue


class TestServiceContainer:
    def test_basics(self) -> None:
        factory = ServiceFactory()
        factory.add_service(ExampleServices.CAT_1, make_cat)
        factory.add_groups(
            (ExampleServiceGroups.CAT, make_cat),
            (ExampleServiceGroups.CAT, make_cat),
        )
        container = ServiceContainer(factory)

        # Just calling this for completeness right now
        container.get_service_ids()

        cat = container.get_service(ExampleServices.CAT_1)
        for x in range(10):
            # calls to get_service() are all cached
            assert cat is container.get_service(ExampleServices.CAT_1)

        for x in range(10):
            assert cat is container.get_service_provider(ExampleServices.CAT_1)()

        cats = container.get_service_group_providers(ExampleServiceGroups.CAT)
        for cp in cats:
            c = cp()
            assert c.speak() == "meow"  # type: ignore

    def test_service_inheritance(self) -> None:
        factory = ServiceFactory()
        factory.add_service(ExampleServices.CAT_1, make_cat)
        factory.add_service(ExampleServices.RUSSIAN_BLUE_1, make_russian_blue)
        factory.add_service(ExampleServices.CAT_2, make_russian_blue)
        # the following should fail mypy - the service id guarantees that the service is a
        # RussianBlueService, but the factory creates a CatService
        factory.add_service(ExampleServices.RUSSIAN_BLUE_2, make_cat)  # type: ignore[misc]


class ExampleContext(NamedTuple):
    name: str


class TestContextualServiceContainer:
    def test_basics(self) -> None:
        factory = ServiceFactory()
        factory.add_service(ExampleServices.CAT_1, make_cat)
        factory.add_groups(
            (ExampleServiceGroups.CAT, make_cat),
            (ExampleServiceGroups.CAT, make_cat),
        )
        container = ContextualServiceContainer[ExampleContext](
            container=factory,
            context_provider=lambda: ExampleContext("123"),
        )

        # Just calling this for completeness right now
        container.get_service_ids()

        cat = container.get_service(ExampleServices.CAT_1)
        for x in range(10):
            # calls to get_service() are all cached
            assert cat is container.get_service(ExampleServices.CAT_1)

        for x in range(10):
            assert cat is container.get_service_provider(ExampleServices.CAT_1)()

        cats = container.get_service_group_providers(ExampleServiceGroups.CAT)
        for cp in cats:
            c = cp()
            assert c.speak() == "meow"
