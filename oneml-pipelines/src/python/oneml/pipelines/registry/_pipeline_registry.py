from typing import Callable, Dict, FrozenSet, Tuple, TypeAlias

from oneml.pipelines.session import PipelineSessionClient

PipelineProvider: TypeAlias = Callable[[], PipelineSessionClient]


class PipelineRegistry:
    _providers: Dict[str, PipelineProvider]

    def __init__(self) -> None:
        self._providers = {}

    def register_pipeline_providers(
        self,
        providers: Tuple[Tuple[str, PipelineProvider], ...],
    ) -> None:
        for name, provider in providers:
            self.register_pipeline_provider(name, provider)

    def register_pipeline_provider(
        self,
        name: str,
        provider: Callable[[], PipelineSessionClient],
    ) -> None:
        self._providers[name] = provider

    def create_session(self, name: str) -> PipelineSessionClient:
        if name not in self._providers:
            raise PipelineProviderNotFoundError(name, frozenset(self._providers.keys()))
        return self._providers[name]()


PipelineRegistryPlugin: TypeAlias = Callable[[PipelineRegistry], None]


class PipelineProviderNotFoundError(ValueError):
    session_name: str
    available_names: FrozenSet[str]

    def __init__(self, session_name: str, available_names: FrozenSet[str]) -> None:
        self.session_name = session_name
        self.available_names = available_names
        super().__init__(
            f"Session provider not found for session name {session_name}. Available names: "
            f"{', '.join(available_names)}"
        )
