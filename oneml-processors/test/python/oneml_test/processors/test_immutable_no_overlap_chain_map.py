from typing import Any, TypeVar

import pytest

from oneml.processors.utils import ImmutableNoOverlapChainMap


def test_init() -> None:
    # Test that the class is initialized correctly
    chain_map = ImmutableNoOverlapChainMap({"a": 1}, {"b": 2})
    assert chain_map["a"] == 1
    assert chain_map["b"] == 2


def test_no_overlap() -> None:
    # Test that overlapping keys raise an error
    with pytest.raises(ValueError):
        ImmutableNoOverlapChainMap({"a": 1}, {"a": 2})


def test_contains() -> None:
    # Test the __contains__ method
    chain_map = ImmutableNoOverlapChainMap({"a": 1}, {"b": 2})
    assert "a" in chain_map
    assert "b" in chain_map
    assert "c" not in chain_map


def test_iter() -> None:
    # Test the __iter__ method
    chain_map = ImmutableNoOverlapChainMap({"a": 1}, {"b": 2})
    assert set(chain_map) == {"a", "b"}


def test_len() -> None:
    # Test the __len__ method
    chain_map = ImmutableNoOverlapChainMap({"a": 1}, {"b": 2})
    assert len(chain_map) == 2


K = TypeVar("K")
V = TypeVar("V")


class Dict(dict[K, V]):
    getitem_counter: int

    def __getitem__(self, k: K) -> V:
        self.getitem_counter += 1
        return super().__getitem__(k)

    def reset_getitem_counter(self) -> None:
        self.getitem_counter = 0


def test_getitem_not_called_on_input_maps() -> None:
    # Create CountedDict instances
    dict1 = Dict(a=1)
    dict2 = Dict(b=2)

    dict1.reset_getitem_counter()
    dict2.reset_getitem_counter()
    chain_map = ImmutableNoOverlapChainMap(dict1, dict2)
    assert dict1.getitem_counter == 0
    assert dict2.getitem_counter == 0

    dict1.reset_getitem_counter()
    dict2.reset_getitem_counter()
    chain_map["a"]
    assert dict1.getitem_counter == 1
    assert dict2.getitem_counter == 0

    dict1.reset_getitem_counter()
    dict2.reset_getitem_counter()
    with pytest.raises(KeyError):
        chain_map["c"]
    assert dict1.getitem_counter == 0
    assert dict2.getitem_counter == 0

    dict1.reset_getitem_counter()
    dict2.reset_getitem_counter()
    assert dict(chain_map) == dict(a=1, b=2)
    assert dict1.getitem_counter == 1
    assert dict2.getitem_counter == 1
