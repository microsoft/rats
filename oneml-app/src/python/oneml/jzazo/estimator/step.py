from collections import UserDict
from typing import Any, Dict, Generic, List

import numpy as np

from .processor import Estimator, Transformer, TransformerProvider


class ArrayLike:
    pass


class Vector(ArrayLike):
    pass


class Matrix(ArrayLike):
    pass


class Output(UserDict[str, Generic[Any]]):
    pass


class Predictions:
    pass


class Model:
    pass


class Dataset:
    pass


class DataLoader:
    def __init__(self, X: Matrix, Y: Vector, batch_size: int) -> None:
        self.X = X
        self.Y = Y
        self.batch_size = batch_size


class Trainer:
    def predict(self, model: Model, dataloaders: List[DataLoader]) -> Predictions:
        pass

    def fit(self, model: Model, dataloader: DataLoader) -> Predictions:
        pass


class StandardizeEval(Transformer):
    _mean: Vector
    _scale: Vector

    def __init__(self, mean: Vector, scale: Vector) -> None:
        super().__init__()
        self._mean = mean
        self._scale = scale

    def process(self, X: Matrix) -> Output:
        return {"Z": (X - self._mean) / self._scale}


class StandardizeTrain(Estimator):
    _eval_type = StandardizeEval
    _eval_args = ["mean", "scale"]
    mean: Vector
    scale: Matrix

    def process(self, X: Matrix) -> Output:
        mean = np.mean(X, axis=1)
        scale = np.std(X, axis=1)
        eval_tf = self.eval_transformer(mean, scale)
        Z = eval_tf.process(X)
        return {"Z": Z, "mean": mean, "scale": scale}


class FormatDataloader(Transformer):
    def __init__(self, batch_size: int) -> None:
        super().__init__()
        self.batch_size = batch_size

    def process(self, X: Matrix, Y: Vector) -> Dict[str, DataLoader]:
        return {"dataloader": DataLoader(X, Y, self.batch_size)}


class ModelEval(Transformer):
    model: Model
    trainer: Trainer

    def __init__(self, model: Model, trainer: Trainer) -> None:
        super().__init__()
        self.model = model
        self.trainer = trainer

    def process(self, dataloaders: List[DataLoader]) -> Output:
        return {"Z": self.trainer.predict(self.model, dataloaders)}


class ModelTrain(Estimator):
    _transformer_provider = TransformerProvider(ModelEval, trainer=trainer)

    model: Model
    trainer: Trainer = Trainer()

    def __init__(self, model: Model, trainer: Trainer) -> None:
        super().__init__()
        self.model = model
        self.trainer = trainer

    def process(self, dataloader: DataLoader) -> Output:
        self.trainer.fit(self.model, dataloader)
        eval_transformer = self.get_transformer(model=self.model, trainer=self.trainer)
        predictions = eval_transformer.process(dataloader)
        return {"predictions": predictions, "model": self.model}
