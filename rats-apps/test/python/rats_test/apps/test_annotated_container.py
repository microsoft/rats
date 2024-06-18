# type: ignore[reportUninitializedInstanceVariable]
import pytest

from rats import apps
from rats_test.apps import example


class TestAnnotatedContainer:
    _app_1: example.ExampleApp
    _app_fallback_1: example.ExampleApp
    _app_fallback_2: example.ExampleApp
    _app_fallback_3: example.ExampleApp
    _app_groups_1: example.ExampleApp
    _app_groups_2: example.ExampleApp

    def setup_method(self) -> None:
        self._app_1 = example.ExampleApp()
        self._app_fallback_1 = example.ExampleApp(
            example.ExampleFallbackPlugin1,
        )
        self._app_fallback_2 = example.ExampleApp(
            example.ExampleFallbackPlugin1,
            example.ExampleFallbackPlugin2,
        )
        self._app_fallback_3 = example.ExampleApp(
            example.ExampleFallbackPlugin1,
            example.ExampleFallbackPlugin3,
        )
        self._app_groups_1 = example.ExampleApp(
            example.ExampleGroupsPlugin1,
        )
        self._app_groups_2 = example.ExampleApp(
            example.ExampleGroupsPlugin1,
            example.ExampleGroupsPlugin2,
        )

    def test_service_retrieval_via_unnamed_services(self) -> None:
        c1t1 = self._app_1.get(example.DummyContainerServiceIds.C1T1)
        c1t2 = self._app_1.get(example.DummyContainerServiceIds.C1T2)
        c1t2a = self._app_1.get(example.DummyContainerServiceIds.C1T2a)
        c1t1b = self._app_1.get(example.DummyContainerServiceIds.C1T1b)
        c2t1 = self._app_1.get(example.DummyContainerServiceIds.C2T1)
        assert c1t1.get_tag() == "c1.s1:t1"
        assert c1t2.get_tag() == "c1.s2:t2"
        assert c1t2a is not c1t2
        assert c2t1.get_tag() == "c2.s1:t1"
        assert c1t1b is c2t1

    def test_service_retrieval(self) -> None:
        storage = self._app_1.get(example.ExampleIds.STORAGE)
        storage.save("msg", "hello")
        assert storage.load("msg") == "hello"

    def test_service_retrieval_is_cached(self) -> None:
        storage_1 = self._app_1.get(example.ExampleIds.STORAGE)
        storage_1.save("msg", "hello")
        assert storage_1.load("msg") == "hello"

        storage_2 = self._app_1.get(example.ExampleIds.STORAGE)
        assert storage_2.load("msg") == "hello"

    def test_service_retrieval_404(self) -> None:
        with pytest.raises(apps.ServiceNotFoundError):
            self._app_1.get(example.ExampleIds.OTHER_STORAGE)

    def test_service_fallback(self) -> None:
        # app_2 has a plugin that defines a fallback service
        fallback = self._app_fallback_1.get(example.ExampleIds.OTHER_STORAGE)
        assert fallback.settings.storage_account == "other[fallback]"

        primary = self._app_fallback_2.get(example.ExampleIds.OTHER_STORAGE)
        assert primary.settings.storage_account == "other"

    def test_duplicate_service(self) -> None:
        with pytest.raises(apps.DuplicateServiceError):
            self._app_1.get(example.ExampleIds.DUPLICATE_SERVICE)

    def test_config_retrieval(self) -> None:
        settings = self._app_1.get(example.ExampleIds.CONFIGS.STORAGE)
        assert settings.storage_account == "default"

    def test_config_retrieval_404(self) -> None:
        with pytest.raises(apps.ServiceNotFoundError):
            self._app_1.get(example.ExampleIds.CONFIGS.OTHER_STORAGE)

    def test_config_retrieval_is_cached(self) -> None:
        first = self._app_1.get(example.ExampleIds.CONFIGS.RANDOM_STORAGE)
        for _ in range(100):
            assert first == self._app_1.get(example.ExampleIds.CONFIGS.RANDOM_STORAGE)

    def test_config_fallback(self) -> None:
        # app_2 has a plugin that defines a fallback service
        fallback = self._app_fallback_1.get(example.ExampleIds.CONFIGS.OTHER_STORAGE)
        assert fallback.storage_account == "other[fallback]"

        primary = self._app_fallback_3.get(example.ExampleIds.CONFIGS.OTHER_STORAGE)
        assert primary.storage_account == "other"

    def test_duplicate_config(self) -> None:
        with pytest.raises(apps.DuplicateServiceError):
            self._app_1.get(example.ExampleIds.CONFIGS.DUPLICATE)

    def test_group_retrieval(self) -> None:
        storage_group_1 = self._app_groups_1.get_group(example.ExampleIds.GROUPS.STORAGE)
        assert len(list(storage_group_1)) == 2

        storage_group_2 = self._app_groups_2.get_group(example.ExampleIds.GROUPS.STORAGE)
        assert len(list(storage_group_2)) == 1

        assert (
            len(list(self._app_groups_2.get_group(example.ExampleIds.GROUPS.OTHER_STORAGE))) == 0
        )

    def test_has_apis(self) -> None:
        assert self._app_1.has(example.ExampleIds.STORAGE)
        assert self._app_groups_1.has_group(example.ExampleIds.GROUPS.STORAGE)
        assert self._app_1.has(example.ExampleIds.CONFIGS.STORAGE)
        assert self._app_1.has_namespace(
            apps.ProviderNamespaces.SERVICES, example.ExampleIds.STORAGE
        )

        assert not self._app_1.has(example.ExampleIds.OTHER_STORAGE)
        assert not self._app_1.has_group(example.ExampleIds.GROUPS.OTHER_STORAGE)
        assert not self._app_1.has(example.ExampleIds.CONFIGS.OTHER_STORAGE)
        assert not self._app_1.has_namespace(
            apps.ProviderNamespaces.SERVICES, example.ExampleIds.OTHER_STORAGE
        )
