from typing import NamedTuple

from oneml.services import ContextualServiceContainer, ServiceContainer, ServiceFactory

from ._examples import ExampleServiceGroups, ExampleServices, make_cat


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
        for _ in range(10):
            # calls to get_service() are all cached
            assert cat is container.get_service(ExampleServices.CAT_1)

        for _ in range(10):
            assert cat is container.get_service_provider(ExampleServices.CAT_1)()

        cats = container.get_service_group_providers(ExampleServiceGroups.CAT)
        for cp in cats:
            c = cp()
            assert c.speak() == "meow"  # type: ignore


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
        for _x in range(10):
            # calls to get_service() are all cached
            assert cat is container.get_service(ExampleServices.CAT_1)

        for _x in range(10):
            assert cat is container.get_service_provider(ExampleServices.CAT_1)()

        cats = container.get_service_group_providers(ExampleServiceGroups.CAT)
        for cp in cats:
            c = cp()
            assert c.speak() == "meow"
