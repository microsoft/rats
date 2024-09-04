from rats import apps

from ._dummies import ITag, Tag


@apps.autoscope
class _PrivateIds:
    C1S1B = apps.ServiceId[ITag]("c1s1b")
    C1S1C = apps.ServiceId[ITag]("c1s1c")
    C1S2A = apps.ServiceId[ITag]("c1s2a")
    C1S2B = apps.ServiceId[ITag]("c1s2b")


class DummyContainer1(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    # Declaring a service without a service id.  The id will be automatically generated from the
    # fully qualified name of the method.
    @apps.autoid_service
    def unnamed_service(self) -> ITag:
        return Tag("c1.s1")

    # Declaring a service with a private service id.  Will be made public below.
    @apps.service(_PrivateIds.C1S1B)
    def c1s1b(self) -> ITag:
        # Calling a service by its method name.
        return self._app.get(apps.autoid(self.unnamed_service))

    @apps.service(_PrivateIds.C1S1C)
    def c1s1c(self) -> ITag:
        # Within a container, you can also directly call the service method.
        # But this version is not cached by apps.Container
        return self.unnamed_service()

    # Declaring a service with multiple service ids.
    # Each service id should be cached separately.
    @apps.service(_PrivateIds.C1S2A)
    @apps.service(_PrivateIds.C1S2B)
    def c1s2(self) -> ITag:
        return Tag("c1.s2")

    @apps.autoid_service
    def c2s1a(self) -> ITag:
        # Calling a service from another container using its public service id.
        return self._app.get(DummyContainerServiceIds.C2S1B)


class DummyContainer2(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    # Declaring a service without a service id.  We are using a method name already used in
    # DummyContainer1, to test that they are not confused.
    @apps.autoid_service
    def unnamed_service(self) -> ITag:
        return Tag("c2.s1")


class DummyContainer(apps.Container):
    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.container()
    def _dummies(self) -> apps.Container:
        return apps.CompositeContainer(
            DummyContainer1(self._app),
            DummyContainer2(self._app),
        )


# Declaring public service ids for the services we want to expose outside this module.
# This is the only class defined in this module that would be exposed outside the package.
class DummyContainerServiceIds:
    C1S1A = apps.autoid(DummyContainer1.unnamed_service)
    C1S1B = _PrivateIds.C1S1B
    C1S1C = _PrivateIds.C1S1C

    C1S2A = _PrivateIds.C1S2A
    C1S2B = _PrivateIds.C1S2B

    C2S1A = apps.autoid(DummyContainer1.c2s1a)
    C2S1B = apps.autoid(DummyContainer2.unnamed_service)
