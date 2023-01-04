from dataclasses import dataclass


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
