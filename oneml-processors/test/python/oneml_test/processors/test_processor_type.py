from multiprocessing import Value

import pytest

from oneml.processors.dag import IProcess
from oneml.processors.ux import Task


class Processor1:
    def process(self) -> None:
        ...


class Processor2(IProcess):
    def process(self) -> None:
        ...


@pytest.fixture(params=[Processor1, Processor2])
def processor_type(request: pytest.FixtureRequest) -> type:
    return request.param


class NonProcessor1:
    def wrong_method_name_process(self) -> None:
        ...


class NonProcessor2(IProcess):
    def wrong_method_name_process(self) -> None:
        ...


@pytest.fixture(params=[NonProcessor1, NonProcessor2])
def non_processor_type(request: pytest.FixtureRequest) -> type:
    return request.param


def test_create_task(processor_type: type) -> None:
    Task(processor_type)


def test_create_task_with_wrong_method_name(non_processor_type: type) -> None:
    with pytest.raises(ValueError):
        Task(non_processor_type)
