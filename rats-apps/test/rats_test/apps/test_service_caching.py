from rats import apps

from .example import DummyContainerServiceIds, ExampleApp, ExampleIds


class TestServiceCaching:
    _app: ExampleApp

    def setup_method(self) -> None:
        self._app = ExampleApp()

    def test_caching_of_multiple_service_calls(self) -> None:
        # service declared with autoid_service
        c1s1a = self._app.get(DummyContainerServiceIds.C1S1A)
        c1s1a_ = self._app.get(DummyContainerServiceIds.C1S1A)

        # the object created in the first call should be cached
        assert c1s1a is c1s1a_

        # service declared with given service id.  internally, it calls
        # the same service as C1S1A, so it should be cached as well.
        c1s1b = self._app.get(DummyContainerServiceIds.C1S1B)

        assert c1s1b is c1s1a

        # service declared with given service id.  internally, it calls the method behind C1S1A,
        # but not via the service id.  This should be a separate object, but cached between the
        # following two calls.
        c1s1c = self._app.get(DummyContainerServiceIds.C1S1C)
        c1s1c_ = self._app.get(DummyContainerServiceIds.C1S1C)

        assert c1s1c is not c1s1a
        assert c1s1c is c1s1c_

        # The tags the two objects should be identical:
        assert c1s1a.get_tag() == "c1.s1"
        assert c1s1c.get_tag() == "c1.s1"

    def test_caching_of_multiple_service_ids(self) -> None:
        # two service ids decorating the same method
        c1s2a = self._app.get(DummyContainerServiceIds.C1S2A)
        c1s2a_ = self._app.get(DummyContainerServiceIds.C1S2A)
        c1s2b = self._app.get(DummyContainerServiceIds.C1S2B)
        c1s2b_ = self._app.get(DummyContainerServiceIds.C1S2B)

        # multiple calls using the same service id should return the same object
        assert c1s2a is c1s2a_
        assert c1s2b is c1s2b_

        # but calls using different service ids should return different objects
        assert c1s2a is not c1s2b

        # the tags the two objects should be identical:
        assert c1s2a.get_tag() == "c1.s2"
        assert c1s2b.get_tag() == "c1.s2"

    def test_caching_of_service_calls_between_containers(self) -> None:
        # C2S1A calls C2S1B, which is a service in another container.
        c2s1a = self._app.get(DummyContainerServiceIds.C2S1A)
        c2s1a_ = self._app.get(DummyContainerServiceIds.C2S1A)
        c2s1b = self._app.get(DummyContainerServiceIds.C2S1B)
        c2s1b_ = self._app.get(DummyContainerServiceIds.C2S1B)

        # All calls should return the same object
        assert c2s1a is c2s1a_
        assert c2s1b is c2s1b_
        assert c2s1a is c2s1b

        assert c2s1a.get_tag() == "c2.s1"

    def test_caching_of_factory_services(self) -> None:
        f1 = self._app.get(DummyContainerServiceIds.TAG_FACTORY_1)
        f1_ = self._app.get(DummyContainerServiceIds.TAG_FACTORY_1)
        f2 = self._app.get(DummyContainerServiceIds.TAG_FACTORY_2)
        f2_ = self._app.get(DummyContainerServiceIds.TAG_FACTORY_2)

        # multiple calls using the same service should return the same factory object
        assert f1 is f1_
        assert f2 is f2_

        # but calls using different service ids should return different objects
        assert f1 is not f2

        # and multiple calls to the factories themselves should return different objects
        t1a = f1("f1")
        t1b = f1("f1")
        t2a = f2("f2")
        t2b = f2("f2")

        assert t1a is not t1b
        assert t2a is not t2b

        assert t1a.get_tag() == "f1"
        assert t1b.get_tag() == "f1"

        assert t2a.get_tag() == "f2"
        assert t2b.get_tag() == "f2"

    def test_caching_of_service_groups(self) -> None:
        clients1 = list(self._app.get_group(ExampleIds.GROUPS.STORAGE))
        clients2 = list(self._app.get_group(ExampleIds.GROUPS.STORAGE))
        clients3 = list(self._app.get_namespaced_group(
            apps.ProviderNamespaces.FALLBACK_GROUPS,
            ExampleIds.GROUPS.STORAGE,
        ))

        assert len(clients1) == 2
        assert len(clients3) == 2
        assert len(clients2) == 2
        assert clients1 == clients2
