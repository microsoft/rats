from collections import defaultdict
from typing import Any

from rats.services import IExecutable, ServiceId, executable
from rats.services._executables import T_ExecutableType


class Triggers:
    # TODO: I think this actually goes in our stdlib under rats.testing or some such
    _state: dict[ServiceId[Any], int]

    def __init__(self) -> None:
        self._state = defaultdict(int)

    def exe(self, exe_id: ServiceId[T_ExecutableType]) -> IExecutable:
        def do() -> None:
            self._state[exe_id] += 1

        return executable(do)

    def get(self, exe_id: ServiceId[T_ExecutableType]) -> int:
        return self._state[exe_id]


class CatService:
    def speak(self) -> str:
        return "meow"


class RussianBlueService(CatService):
    def speak(self) -> str:
        return "meow"

    def also_speak(self) -> str:
        return "purr"


class DogExecutable(IExecutable):
    def execute(self) -> None:
        print("woof")


class ExampleServices:
    CAT_1 = ServiceId[CatService]("cat.1")
    CAT_2 = ServiceId[CatService]("cat.2")
    RUSSIAN_BLUE_1 = ServiceId[RussianBlueService]("russian-blue.1")
    RUSSIAN_BLUE_2 = ServiceId[RussianBlueService]("russian-blue.2")
    DOG_1 = ServiceId[DogExecutable]("dog.1")
    DOG_2 = ServiceId[DogExecutable]("dog.2")


class ExampleServiceGroups:
    CAT = ServiceId[CatService]("cat")
    DOG = ServiceId[DogExecutable]("dog")


def make_cat() -> CatService:
    return CatService()


def make_russian_blue() -> RussianBlueService:
    return RussianBlueService()


def make_dog() -> DogExecutable:
    return DogExecutable()
