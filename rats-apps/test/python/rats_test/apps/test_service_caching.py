from .example import DummyContainerServiceIds, ExampleApp


class TestServiceCaching:
    _app: ExampleApp = ExampleApp()

    def test_service_caching(self) -> None:
        c1s1a = self._app.get(DummyContainerServiceIds.C1S1A)
        c1s1a_ = self._app.get(DummyContainerServiceIds.C1S1A)
        c1s1b = self._app.get(DummyContainerServiceIds.C1S1B)
        c1s1b_ = self._app.get(DummyContainerServiceIds.C1S1B)
        c1s1c = self._app.get(DummyContainerServiceIds.C1S1C)
        c1s1c_ = self._app.get(DummyContainerServiceIds.C1S1C)

        assert c1s1a is c1s1a_
        assert c1s1b is c1s1b_
        assert c1s1c is c1s1c_
        assert c1s1a.get_tag() == "c1.s1"
        assert c1s1b.get_tag() == "c1.s1"
        assert c1s1c.get_tag() == "c1.s1"
        assert c1s1a is c1s1b
        assert c1s1a is not c1s1c

        c1s2a = self._app.get(DummyContainerServiceIds.C1S2A)
        c1s2a_ = self._app.get(DummyContainerServiceIds.C1S2A)
        c1s2b = self._app.get(DummyContainerServiceIds.C1S2B)
        c1s2b_ = self._app.get(DummyContainerServiceIds.C1S2B)

        assert c1s2a is c1s2a_
        assert c1s2b is c1s2b_
        assert c1s2a.get_tag() == "c1.s2"
        assert c1s2b.get_tag() == "c1.s2"
        assert c1s2a is not c1s2b

        c2s1a = self._app.get(DummyContainerServiceIds.C2S1A)
        c2s1a_ = self._app.get(DummyContainerServiceIds.C2S1A)
        c2s1b = self._app.get(DummyContainerServiceIds.C2S1B)
        c2s1b_ = self._app.get(DummyContainerServiceIds.C2S1B)

        assert c2s1a is c2s1a_
        assert c2s1b is c2s1b_
        assert c2s1a.get_tag() == "c2.s1"
        assert c2s1b.get_tag() == "c2.s1"
        assert c2s1a is c2s1b
