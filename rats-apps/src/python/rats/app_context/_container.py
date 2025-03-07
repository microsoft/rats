import logging
from collections.abc import Iterator
from functools import partial
from typing import Generic, final

from rats import apps

from ._collection import Collection
from ._context import T_ContextType

logger = logging.getLogger(__name__)


@final
class Container(apps.Container, Generic[T_ContextType]):
    """
    A [rats.apps.Container][] that provides services from a [rats.app_context.Collection][].
    """
    _cls: type[T_ContextType]
    _namespace: str
    _collection: Collection[T_ContextType]

    def __init__(
        self,
        cls: type[T_ContextType],
        namespace: str,
        collection: Collection[T_ContextType],
    ) -> None:
        self._cls = cls
        self._namespace = namespace
        self._collection = collection

    @apps.container()
    def _contexts(self) -> apps.Container:
        containers: list[apps.Container] = []

        def _provider(_service_id: apps.ServiceId[T_ContextType]) -> T_ContextType:
            contexts = self._collection.decoded_values(self._cls, _service_id)
            if len(contexts) > 1:
                raise apps.DuplicateServiceError(_service_id)
            if len(contexts) == 0:
                raise apps.ServiceNotFoundError(_service_id)

            return contexts[0]

        def _group_provider(_service_id: apps.ServiceId[T_ContextType]) -> Iterator[T_ContextType]:
            yield from self._collection.decoded_values(self._cls, _service_id)

        if self._namespace in [apps.ProviderNamespaces.SERVICES, apps.ProviderNamespaces.FALLBACK_SERVICES]:
            for service_id in self._collection.service_ids():
                containers.append(
                    apps.StaticContainer(
                        apps.StaticProvider[T_ContextType](
                            namespace=self._namespace,
                            service_id=service_id,
                            call=partial(_provider, service_id),
                        ),
                    )
                )
        else:
            for service_id in self._collection.service_ids():
                containers.append(
                    apps.StaticContainer(
                        apps.StaticProvider[T_ContextType](
                            namespace=self._namespace,
                            service_id=service_id,
                            provider=partial(_group_provider, service_id),  # type: ignore
                        ),
                    )
                )

        return apps.CompositeContainer(*containers)
