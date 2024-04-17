from rats import apps

from ._dummies import ITag, Tag1, Tag2


@apps.autoscope
class _PrivateIds:
    SERVICE2 = apps.ServiceId[Tag2]("service2")
    C1T1 = apps.ServiceId[ITag]("c1t1")
    C1T2a = apps.ServiceId[Tag2]("c1t2a")


class DummyContainer1(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    # Declaring a service without a service id.  The id will be automatically generated from the
    # fully qualified name of the method.
    @apps.autoid_service
    def unnamed_service1(self) -> Tag1:
        return Tag1("c1.s1")

    # Declaring a service with a private service id.
    @apps.service(_PrivateIds.SERVICE2)
    def unnamed_service2(self) -> Tag2:
        return Tag2("c1.s2")

    # Declaring a service with a private service id.  Will be made public below.
    @apps.service(_PrivateIds.C1T1)
    def tag1(self) -> Tag1:
        # Calling a service by its method name.
        return self._app.get(apps.method_service_id(self.unnamed_service1))

    # Again without a service id, but this service will be made public below.
    @apps.autoid_service
    def tag2(self) -> Tag2:
        # Calling a service using the private service id.
        return self._app.get(_PrivateIds.SERVICE2)

    @apps.service(_PrivateIds.C1T2a)
    def tag2a(self) -> Tag2:
        # Within a container, you can also directly call the service method.
        return self.unnamed_service2()

    @apps.autoid_service
    def tag1b(self) -> Tag1:
        # Calling a service from another container using its public service id.
        return self._app.get(DummyContainerServiceIds.C2T1)


class DummyContainer2(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    # Declaring a service without a service id.  We are using a method name already used in
    # DummyContainer1, to test that they are not confused.
    @apps.autoid_service
    def unnamed_service1(self) -> Tag1:
        return Tag1("c2.s1")

    @apps.autoid_service
    def tag1(self) -> Tag1:
        return self._app.get(apps.method_service_id(self.unnamed_service1))


class DummyContainer(apps.CompositeContainer):
    def __init__(self, app: apps.Container) -> None:
        super().__init__(DummyContainer1(app), DummyContainer2(app))


# Declaring public service ids for the services we want to expose outside this module.
# This is the only class defined in this module that would be exposed outside the package.
class DummyContainerServiceIds:
    # Take a private id and make it public.
    C1T1 = _PrivateIds.C1T1
    # Make public ids for a services with auto-generated ids.
    C1T2 = apps.method_service_id(DummyContainer1.tag2)
    C1T1b = apps.method_service_id(DummyContainer1.tag1b)
    C2T1 = apps.method_service_id(DummyContainer2.tag1)
    # The same mechanism can be used for services declared with service ids.
    C1T2a = apps.method_service_id(DummyContainer1.tag2a)
