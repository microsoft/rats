from typing import Any

from oneml.services import ContextId, ServiceId, scoped_context_ids, scoped_service_ids


@scoped_context_ids
class CatContexts:
    FOO = ContextId[Any]("foo")
    ANOTHER_FOO = ContextId[Any]("foo")
    BAR = ContextId[Any]("bar")
    SPECIAL_BAR = ContextId[Any]("/special-cat/bar")
    SOMETHING_ELSE = "moo"

    @staticmethod
    def make(name: str) -> ContextId[Any]:
        return ContextId[Any](f"/special-cat/{name}")

    @staticmethod
    def something_else() -> str:
        return "moo"


@scoped_context_ids
class DogContexts:
    FOO = ContextId[Any]("foo")
    ANOTHER_FOO = ContextId[Any]("foo")
    BAR = ContextId[Any]("bar")


@scoped_service_ids
class CatServices:
    FOO = ServiceId[Any]("foo")
    ANOTHER_FOO = ServiceId[Any]("foo")
    BAR = ServiceId[Any]("bar")
    SPECIAL_BAR = ServiceId[Any]("/special-cat/bar")
    SOMETHING_ELSE = "moo"

    @staticmethod
    def make(name: str) -> ServiceId[Any]:
        return ServiceId[Any](f"/special-cat/{name}")

    @staticmethod
    def something_else() -> str:
        return "moo"


@scoped_service_ids
class DogServices:
    FOO = ServiceId[Any]("foo")
    ANOTHER_FOO = ServiceId[Any]("foo")
    BAR = ServiceId[Any]("bar")


class TestScopes:
    def test_contexts(self) -> None:
        assert CatContexts.FOO == CatContexts.FOO
        assert CatContexts.FOO == CatContexts.ANOTHER_FOO
        assert CatContexts.FOO != CatContexts.BAR
        assert CatContexts.make("bar") == CatContexts.SPECIAL_BAR
        assert CatContexts.something_else() == "moo"
        assert CatContexts.SOMETHING_ELSE == "moo"

        assert DogContexts.FOO == DogContexts.FOO
        assert DogContexts.FOO == DogContexts.ANOTHER_FOO
        assert DogContexts.FOO != DogContexts.BAR

        assert CatContexts.FOO != DogContexts.FOO
        assert CatContexts.FOO != DogContexts.ANOTHER_FOO
        assert CatContexts.FOO != DogContexts.BAR

    def test_services(self) -> None:
        assert CatServices.FOO == CatServices.FOO
        assert CatServices.FOO == CatServices.ANOTHER_FOO
        assert CatServices.FOO != CatServices.BAR
        assert CatServices.make("bar") == CatServices.SPECIAL_BAR
        assert CatServices.something_else() == "moo"
        assert CatServices.SOMETHING_ELSE == "moo"

        assert DogServices.FOO == DogServices.FOO
        assert DogServices.FOO == DogServices.ANOTHER_FOO
        assert DogServices.FOO != DogServices.BAR

        assert CatServices.FOO != DogServices.FOO
        assert CatServices.FOO != DogServices.ANOTHER_FOO
        assert CatServices.FOO != DogServices.BAR
