import pytest
from typing_extensions import NamedTuple

from oneml.services import ContextClient, ContextId


class CatContext(NamedTuple):
    spoken_word: str


class TestContextClient:
    def test_basics(self) -> None:
        client = ContextClient()
        with client.open_context(ContextId[CatContext]("cat"), CatContext(spoken_word="meow")):
            provider = client.get_context_provider(ContextId[CatContext]("cat"))
            cat = provider()
            assert cat.spoken_word == "meow"

        with pytest.raises(RuntimeError):
            client.get_context(ContextId[CatContext]("cat"))
