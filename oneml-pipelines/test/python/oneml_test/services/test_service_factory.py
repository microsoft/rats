import pytest

from oneml.services import DuplicateServiceIdError, ServiceFactory, ServiceIdNotFoundError

from ._examples import ExampleServiceGroups, ExampleServices, make_cat


class TestServiceFactory:
    _empty_factory: ServiceFactory
    _factory: ServiceFactory

    def setup_method(self) -> None:
        self._empty_factory = ServiceFactory()
        self._factory = ServiceFactory()
        self._factory.add_service(ExampleServices.CAT_1, make_cat)
        self._factory.add_services(
            (ExampleServices.CAT_2, make_cat),
        )
        self._factory.add_group(ExampleServiceGroups.CAT, make_cat)
        # Just adding the same thing multiple times to test the various APIs
        self._factory.add_groups(
            (ExampleServiceGroups.CAT, make_cat),
            (ExampleServiceGroups.CAT, make_cat),
        )

    def test_basics(self) -> None:
        cat = self._factory.get_service(ExampleServices.CAT_1)
        assert cat.speak() == "meow"

        cats = list(self._factory.get_service_group(ExampleServiceGroups.CAT))
        assert len(cats) > 0

        for group_cat in cats:
            assert group_cat.speak() == "meow"

    def test_misconfigurations(self) -> None:
        with pytest.raises(ServiceIdNotFoundError):
            self._empty_factory.get_service(ExampleServices.CAT_1)

        with pytest.raises(DuplicateServiceIdError):
            # the callback doesn't actually matter
            self._factory.add_service(ExampleServices.CAT_1, make_cat)
