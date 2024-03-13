from rats.services import (
    ContextClient,
    ExecutablesClient,
    ServiceFactory,
    TypedServiceContainer,
    after,
    before,
)

from ._examples import ExampleServices, Triggers, make_dog


class TestExecutablesContainer:
    _triggers: Triggers

    def setup_method(self) -> None:
        self._triggers = Triggers()

    def test_basics(self) -> None:
        ContextClient()
        factory = ServiceFactory()
        factory.add_service(ExampleServices.DOG_1, make_dog)
        factory.add_group(
            before(ExampleServices.DOG_1),
            lambda: self._triggers.exe(before(ExampleServices.DOG_1)),
        )
        factory.add_group(
            after(ExampleServices.DOG_1),
            lambda: self._triggers.exe(after(ExampleServices.DOG_1)),
        )
        container = ExecutablesClient(TypedServiceContainer(factory))
        container.execute_id(ExampleServices.DOG_1)
        container.execute(ExampleServices.DOG_1, factory.get_service(ExampleServices.DOG_1))

        assert self._triggers.get(before(ExampleServices.DOG_1)) == 2
        assert self._triggers.get(after(ExampleServices.DOG_1)) == 2


# Idea:
# - ExecutablesContainer opens contexts
# - we never have to open contexts ourselves
# - but we also don't have the need to make our own contexts
# - only executable contexts exist, they have a uuid and the service id of the exe
# - only way to create a context is to make an executable (just a service id)
# - people don't think about contexts, they think of executables
# - now that contexts and executables have a 1:1 mapping, we can reuse it for before/after events
# - when a context opens, we execute the before() executables that have been added
# - when a context closes, we execute the after() executables that have been added
# - each of those executables also open their own context because they are executed the same way
# - I think we should be able to validate the executable dag and build one dynamically

# let's see if we can implement this with strict TDD. I've never done this before.
