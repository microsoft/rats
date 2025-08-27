from typing import NamedTuple


class KustomizeImage(NamedTuple):
    name: str
    newName: str
    newTag: str

    @property
    def full_name(self) -> str:
        return f"{self.newName}:{self.newTag}"
