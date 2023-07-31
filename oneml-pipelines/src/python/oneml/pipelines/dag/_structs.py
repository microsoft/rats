from typing import Generic, TypeVar

from typing_extensions import NamedTuple

T_PipelinePortDataType = TypeVar("T_PipelinePortDataType")


class PipelineNode(NamedTuple):
    key: str

    def __post_init__(self) -> None:
        parts = self.key.strip("/").split("/")
        if len(parts) < 1:
            raise ValueError("Pipeline node key must be non-empty")

    @property
    def name(self) -> str:
        return self.key.split("/")[-1]


class PipelinePort(NamedTuple, Generic[T_PipelinePortDataType]):
    key: str


class PipelineDataDependency(NamedTuple, Generic[T_PipelinePortDataType]):
    node: PipelineNode
    output_port: PipelinePort[T_PipelinePortDataType]
    input_port: PipelinePort[T_PipelinePortDataType]
