from typing import List

from oneml.services import IExecutable, ServiceId, scoped_service_ids


class OpenAiRunner:
    def query(self, thing: str) -> List[float]:
        return [1, 2, 3]


class AzClient:
    def login(self) -> None:
        pass


class SearchCommand(IExecutable):
    _openai: OpenAiRunner

    def __init__(self, openai: OpenAiRunner) -> None:
        self._openai = openai

    def execute(self) -> None:
        print("hello from the cmd class")
        print(f"some floats: {self._openai.query('halp')}")


class AzLoginCommand(IExecutable):
    _az: AzClient

    def __init__(self, az: AzClient) -> None:
        self._az = az

    def execute(self) -> None:
        print("LOGGING YOU IN!")


@scoped_service_ids
class SearchServices:
    MAIN = ServiceId[IExecutable]("main")
    AZ_LOGIN = ServiceId[IExecutable]("az-login")
    OPENAI = ServiceId[OpenAiRunner]("openai")
