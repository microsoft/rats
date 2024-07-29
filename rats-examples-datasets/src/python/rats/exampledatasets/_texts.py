import uuid
from random import randint
from typing import NamedTuple


class SimpleText(NamedTuple):
    id: str
    body: str


class ExampleTexts:
    def books(self, num: int) -> tuple[tuple[tuple[SimpleText, ...], ...], ...]:
        return tuple(self.chapters(randint(11, 20)) for _ in range(num))

    def chapters(self, num: int) -> tuple[tuple[SimpleText, ...], ...]:
        return tuple(self.paragraphs(randint(11, 20)) for _ in range(num))

    def paragraphs(self, num: int) -> tuple[SimpleText, ...]:
        return tuple(
            [SimpleText(id=str(uuid.uuid4()), body=f"paragraph {i} text") for i in range(num)],
        )
