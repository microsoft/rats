from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineId:
    key: str

    @property
    def name(self) -> str:
        return self.key.split("/")[-1]
