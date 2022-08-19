# type: ignore
# flake8: noqa
from dataclasses import dataclass

import numpy.typing as npt
import sklearn.linear_model
from munch import Munch

from .processors import ProcessingFunc, processor_from_func
from .return_annotation import return_annotation


@processor_from_func
@dataclass
class FittedStandardizer:
    # parameters
    offset: float
    scale: float

    def process(self, features: npt.ArrayLike) -> return_annotation(features=npt.ArrayLike):
        features = (features + self.offset) * self.scale
        return Munch(features=features)


@processor_from_func
@dataclass
class Standardizer(ProcessingFunc):
    def process(
        self, features: npt.ArrayLike
    ) -> return_annotation(fitted=FittedStandardizer, features=npt.ArrayLike):
        offset = -features.mean(axis=0)
        scale = 1.0 / features.std(axis=0)
        f = FittedStandardizer(offset=offset, scale=scale)
        features = f.process(features).features
        return Munch(fitted=f, features=features)


@processor_from_func
@dataclass
class FittedLogisticRegression:
    classes: npt.ArrayLike
    coef: npt.ArrayLike
    intercept: npt.ArrayLike

    def process(self, features: npt.ArrayLike) -> return_annotation(predictions=npt.ArrayLike):
        lr = sklearn.linear_model.LogisticRegression()
        lr.classes_ = self.classes
        lr.coef_ = self.coef
        lr.intercept_ = self.intercept
        predictions = lr.predict(X=features)
        return Munch(predictions=predictions)


@processor_from_func
class LogisticRegression(ProcessingFunc):
    def process(
        self, features: npt.ArrayLike, labels: npt.ArrayLike
    ) -> return_annotation(fitted=FittedLogisticRegression, predictions=npt.ArrayLike):
        lr = sklearn.linear_model.LogisticRegression()
        lr.fit(
            X=features,
            y=labels,
        )
        fitted = FittedLogisticRegression(
            classes=lr.classes_, coef=lr.coef_, intercept=lr.intercept_
        )
        predictions = fitted.process(features).predictions
        return Munch(fitted=fitted, predictions=predictions)
