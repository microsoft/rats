from collections import defaultdict
from typing import Any, Dict

from oneml.services import IExecutable, ServiceId, executable
from oneml.services._executables import T_ExecutableType


class Triggers:
    # TODO: I think this actually goes in our stdlib under oneml.testing or some such
    _state: Dict[ServiceId[Any], int]

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


class DogExecutable(IExecutable):
    def execute(self) -> None:
        print("woof")


class ExampleServices:
    CAT_1 = ServiceId[CatService]("cat.1")
    CAT_2 = ServiceId[CatService]("cat.2")
    DOG_1 = ServiceId[DogExecutable]("dog.1")
    DOG_2 = ServiceId[DogExecutable]("dog.2")


class ExampleServiceGroups:
    CAT = ServiceId[CatService]("cat")
    DOG = ServiceId[DogExecutable]("dog")


def make_cat() -> CatService:
    return CatService()


def make_dog() -> DogExecutable:
    return DogExecutable()