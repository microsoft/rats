from __future__ import annotations

from functools import cache
from typing import Any, Callable, Generic, Hashable, Iterable, Iterator, Mapping, Protocol, TypeVar

from ._frozendict import frozendict
from ._processor import IGetParams, IParamGetterContract, KnownParamsGetter

T = TypeVar("T", covariant=True)


class ISingletonFactoryPromise(Hashable, Generic[T], Protocol):
    @property
    def id(self) -> str:
        ...

    @property
    def type(self) -> type:
        ...


class ISingletonFactory(Generic[T], Protocol):
    @property
    def id(self) -> str:
        ...

    @property
    def type(self) -> type:
        ...

    @property
    def promise(self) -> ISingletonFactoryPromise[T]:
        ...

    def __call__(self) -> T:
        ...


class SingletonFactoryPromise(ISingletonFactoryPromise[T]):
    _id: str
    _type: type

    def __init__(self, id: str, type: type) -> None:
        self._id = id
        self._type = type

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> type:
        return self._type

    def __hash__(self) -> int:
        return hash((self._id, self._type))


class SingletonFactory(ISingletonFactory[T]):
    _promise: ISingletonFactoryPromise[T]
    _func: Callable[[], T]

    def __init__(self, promise: ISingletonFactoryPromise[T], func: Callable[[], T]) -> None:
        self._promise = promise
        self._func = cache(func)

    @property
    def id(self) -> str:
        return self._promise.id

    @property
    def type(self) -> type:
        return self._promise.type

    @property
    def promise(self) -> ISingletonFactoryPromise[T]:
        return self._promise

    def __call__(self) -> T:
        return self._func()


class IRegistryOfSingletonFactories(Protocol):
    def __getitem__(self, id: str) -> ISingletonFactory[Any]:
        ...


class RegistryOfSingletonFactories(IRegistryOfSingletonFactories):
    _d: frozendict[str, ISingletonFactory[Any]]

    def __init__(self, singleton_factories: Iterable[ISingletonFactory[Any]]) -> None:
        self._d = frozendict(**{f.id: f for f in singleton_factories})

    def __getitem__(self, id: str) -> ISingletonFactory[Any]:
        return self._d[id]


class IParamsFromEnvironmentSingletonsContract(IParamGetterContract):
    def fullfill_using_registry(self, registry: IRegistryOfSingletonFactories) -> IGetParams:
        ...


class EmptyParamsFromEnvironmentContract(IParamsFromEnvironmentSingletonsContract):
    def fullfill_using_registry(self, registry: IRegistryOfSingletonFactories) -> IGetParams:
        return KnownParamsGetter()

    def __hash__(self) -> int:
        return hash(type(self))

    def __iter__(self) -> Iterator[str]:
        yield from []


class ParamsFromEnvironmentSingletonsContract(IParamsFromEnvironmentSingletonsContract):
    _param_to_singleton_factory_promise: frozendict[str, ISingletonFactoryPromise[Any]]

    def __init__(self, **param_to_singleton_factory_promise: ISingletonFactoryPromise[Any]):
        self._param_to_singleton_factory_promise = frozendict(param_to_singleton_factory_promise)

    def __iter__(self) -> Iterator[str]:
        """The names of the parameters that will be provided."""
        return iter(self._param_to_singleton_factory_promise)

    def __hash__(self) -> int:
        return hash(self._param_to_singleton_factory_promise)

    def fullfill_using_registry(
        self, registry: IRegistryOfSingletonFactories
    ) -> ParamsFromEnvironmentSingletons:
        param_to_singleton_factory = {
            param_name: registry[promise.id]
            for param_name, promise in self._param_to_singleton_factory_promise.items()
        }
        return ParamsFromEnvironmentSingletons(param_to_singleton_factory)


class ParamsFromEnvironmentSingletons(IGetParams):
    _param_to_singleton_factory: frozendict[str, ISingletonFactory[Any]]

    def __init__(self, param_to_singleton_factory: Mapping[str, ISingletonFactory[Any]]):
        self._param_to_singleton_factory = frozendict(param_to_singleton_factory)

    def __call__(self) -> Mapping[str, Any]:
        return {
            param_name: factory()
            for param_name, factory in self._param_to_singleton_factory.items()
        }

    def __iter__(self) -> Iterator[str]:
        """The names of the parameters that will be provided."""
        return iter(self._param_to_singleton_factory)
