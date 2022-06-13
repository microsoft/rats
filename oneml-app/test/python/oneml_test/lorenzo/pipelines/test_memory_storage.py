from dataclasses import dataclass

import pytest

from oneml.lorenzo.pipelines import DuplicateStorageKeyError, InMemoryStorage


@dataclass(frozen=True)
class FakeThing1:
    name: str


@dataclass(frozen=True)
class FakeThing2:
    name: str


class TestInMemoryStorage:

    def test_basics(self) -> None:
        storage = InMemoryStorage()
        thing1 = FakeThing1(name="fake-thing-1")
        thing2 = FakeThing2(name="fake-thing-2")

        storage.save(FakeThing1, thing1)
        storage.save(FakeThing2, thing2)

        assert storage.load(FakeThing1) == thing1
        assert storage.load(FakeThing2) == thing2

    def test_duplicate_save(self) -> None:
        storage = InMemoryStorage()
        thing1a = FakeThing1(name="fake-thing-1a")
        thing1b = FakeThing1(name="fake-thing-1b")

        storage.save(FakeThing1, thing1a)

        with pytest.raises(DuplicateStorageKeyError):
            storage.save(FakeThing1, thing1b)

