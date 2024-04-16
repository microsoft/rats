from collections.abc import Callable
from typing import Concatenate, ParamSpec, TypeVar

from rats import apps
from rats.processors import ux

T_ServiceType = TypeVar("T_ServiceType")
P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=apps.Container)


def _process_method_to_task_method(
    process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
) -> Callable[[T_Container], ux.UPipeline]:
    class _Processor(ux.IProcess):
        process = process_method

    _Processor.__name__ = process_method.__name__

    def get_task(self: T_Container) -> ux.UPipeline:
        return ux.UTask(_Processor)

    return get_task


def task() -> (
    Callable[
        [Callable[Concatenate[T_Container, P], ux.T_Processor_Output]],
        Callable[[T_Container], ux.UPipeline],
    ]
):
    def wrapper(
        process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
    ) -> Callable[[T_Container], ux.UPipeline]:
        task_method = _process_method_to_task_method(process_method)
        return apps.service()(task_method)

    return wrapper


pipeline = apps.service
