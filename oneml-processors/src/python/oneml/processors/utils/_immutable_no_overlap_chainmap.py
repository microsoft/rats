from collections.abc import Iterable, Iterator, Mapping
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


class ImmutableNoOverlapChainMap(Mapping[K, V]):
    _key_to_map: Mapping[K, Mapping[K, V]]

    def __init__(self, *maps: Mapping[K, V]) -> None:
        self._key_to_map = self._build_key_to_map(maps)

    @classmethod
    def _build_key_to_map(cls, maps: Iterable[Mapping[K, V]]) -> Mapping[K, Mapping[K, V]]:
        key_to_map = dict[K, Mapping[K, V]]()
        duplicates = set()
        for m in maps:
            s = set(m.keys())
            duplicates.update(s.intersection(key_to_map))
            key_to_map.update({k: m for k in s})
        if duplicates:
            raise ValueError(f"Duplicate keys found: {duplicates}")
        return key_to_map

    def __getitem__(self, key: K) -> V:
        m = self._key_to_map[key]
        v = m[key]
        return v

    def __contains__(self, key: object) -> bool:
        return key in self._key_to_map

    def __iter__(self) -> Iterator[K]:
        return self._key_to_map.__iter__()

    def __len__(self) -> int:
        return len(self._key_to_map)
