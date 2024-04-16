from abc import abstractmethod
from collections.abc import Callable
from typing import TypeVar

from rats import apps
from rats.processors import ux

T_Container = TypeVar("T_Container", bound="PipelineContainer")


def subpipeline() -> (
    Callable[
        [Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]],
        Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]],
    ]
):
    def wrapper(
        fn: Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]],
    ) -> Callable[[T_Container], ux.Pipeline[ux.TInputs, ux.TOutputs]]:
        return apps.service()(fn)

    return wrapper


class PipelineContainer(apps.Container):
    @abstractmethod
    def name(self) -> str:
        pass
