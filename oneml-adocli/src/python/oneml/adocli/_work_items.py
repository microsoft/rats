from dataclasses import dataclass


@dataclass(frozen=True)
class AdoWorkItem:
    id: int
    title: str
    description: str
    iteration_path: str
    state: str

    def is_done(self) -> bool:
        return self.state.lower() == "done"
