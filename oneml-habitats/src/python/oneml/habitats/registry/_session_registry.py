from typing import Callable, Dict, Tuple, TypeAlias

from oneml.pipelines.session import PipelineSessionClient

SessionProvider: TypeAlias = Callable[[], PipelineSessionClient]


class PipelineSessionRegistry:

    _providers: Dict[str, SessionProvider]

    def __init__(self) -> None:
        self._providers = {}

    def register_session_providers(
        self,
        providers: Tuple[Tuple[str, SessionProvider], ...],
    ) -> None:
        for name, provider in providers:
            self.register_session_provider(name, provider)

    def register_session_provider(self, name: str, provider: SessionProvider) -> None:
        self._providers[name] = provider

    def create_session(self, name: str) -> PipelineSessionClient:
        return self._providers[name]()
