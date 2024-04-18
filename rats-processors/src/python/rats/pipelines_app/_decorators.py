from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from rats import apps
from rats.processors import ux

T_ServiceType = TypeVar("T_ServiceType")
P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=apps.Container)


def _process_method_to_task_method(
    process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
) -> Callable[[T_Container], ux.UPipeline]:
    """Convert a process method to a method returning a task wrapping over the process method."""

    class _Processor(ux.IProcess):
        process = process_method

    _Processor.__name__ = process_method.__name__

    def get_task(self: T_Container) -> ux.UPipeline:
        return ux.UTask(_Processor)

    get_task.__name__ = process_method.__name__
    get_task.__module__ = process_method.__module__
    get_task.__qualname__ = process_method.__qualname__
    get_task.__doc__ = process_method.__doc__

    return get_task


def task(
    process_method: Callable[Concatenate[T_Container, P], ux.T_Processor_Output],
) -> Callable[[T_Container], ux.UPipeline]:
    """Decorator creating a pipeline service from a process method.

    The pipeline will be a task wrapping over the method.

    The name of the pipeline will be name of the method.
    """
    task_method = _process_method_to_task_method(process_method)
    return apps.autoid_service(task_method)


def pipeline(
    get_pipeline_method: Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]],
) -> Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]:
    """Decorator creating a pipeline service.

    The name of the pipeline will be name of the method.
    """
    name = get_pipeline_method.__name__

    @wraps(get_pipeline_method)
    def get_pipeline_and_rename(
        self: T_Container,
    ) -> ux.Pipeline[ux.TInputs, ux.TOutputs]:
        pipeline = get_pipeline_method(self)
        if pipeline.name != name:
            pipeline = pipeline.decorate(name)
        return pipeline

    return apps.autoid_service(get_pipeline_and_rename)
