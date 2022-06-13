from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TrainerHyperparameters:
    batch_size: int
    learning_rate: float


@dataclass(frozen=True)
class TrainerParameterSearchSpace:
    batch_sizes: Tuple[int, ...]
    learning_rates: Tuple[float, ...]

    def values(self) -> Tuple[TrainerHyperparameters]:
        return tuple([
            TrainerHyperparameters(self.batch_sizes[0], self.learning_rates[0]),
            TrainerHyperparameters(self.batch_sizes[1], self.learning_rates[1]),
            TrainerHyperparameters(self.batch_sizes[2], self.learning_rates[2]),
        ])
