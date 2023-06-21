from dataclasses import dataclass
from typing import Generic, NamedTuple, TypeVar

# TODO: Remove the copies of DataType and PipelineDataNode from app package
PipelinePortDataType = TypeVar("PipelinePortDataType")


@dataclass(frozen=True)
class PipelineNode:
    key: str

    def __post_init__(self) -> None:
        parts = self.key.strip("/").split("/")
        if len(parts) < 1:
            raise ValueError("Pipeline node key must be non-empty")

    @property
    def name(self) -> str:
        return self.key.split("/")[-1]


@dataclass(frozen=True)
class PipelinePort(Generic[PipelinePortDataType]):
    key: str


@dataclass(frozen=True)
class PipelineDataDependency(Generic[PipelinePortDataType]):
    node: PipelineNode
    output_port: PipelinePort[PipelinePortDataType]
    input_port: PipelinePort[PipelinePortDataType]


class PipelineSessionId(NamedTuple):
    key: str


# TODO: tried converting PipelineNode to a NamedTuple, but it broke the type checking
class PipelineNodeId(NamedTuple):
    key: str
