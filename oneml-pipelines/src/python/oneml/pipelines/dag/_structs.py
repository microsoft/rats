from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineNode:
    key: str

    @property
    def name(self) -> str:
        return self.key.split("/")[-1]
