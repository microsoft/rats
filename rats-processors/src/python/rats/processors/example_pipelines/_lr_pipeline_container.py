from collections.abc import Sequence
from typing import NamedTuple, cast

import pandas as pd
from sklearn.linear_model import LogisticRegression as LR

from rats import apps
from rats import processors as rp
from rats.processors import typing as rpt


class LRModel(NamedTuple):
    bare_model: LR
    feature_names: tuple[str, ...]
    category_names: tuple[str, ...]


class _SanitizeLabelsOutput(NamedTuple):
    y: pd.Series  # [int] category indices [0, N)
    number_of_labels_in_training: int


class _LRTrainOutput(NamedTuple):
    model: LRModel
    number_of_samples_in_training: int


class _LRPredictOutput(NamedTuple):
    logits: pd.DataFrame  # [float], columns are category names


class TrainInputs(rpt.Inputs):
    category_names: rpt.InPort[tuple[str, ...]]
    x: rpt.InPort[pd.DataFrame]  # [float], column names become feature names
    y: rpt.InPort[pd.Series]  # [int], category indices


class TrainOutputs(rpt.Outputs):
    model: rpt.OutPort[LRModel]
    number_of_labels_in_training: rpt.OutPort[int]
    number_of_samples_in_training: rpt.OutPort[int]


TrainPl = rpt.Pipeline[TrainInputs, TrainOutputs]


class PredictInputs(rpt.Inputs):
    model: rpt.InPort[LRModel]
    x: rpt.InPort[pd.DataFrame]


class PredictOutputs(rpt.Outputs):
    logits: rpt.OutPort[pd.DataFrame]


PredictPl = rpt.Pipeline[PredictInputs, PredictOutputs]


class LRPipelineContainer(rp.PipelineContainer):
    @rp.task
    def sanitize_labels(
        self,
        category_names: Sequence[str],  # order will determine category index in output.
        y: pd.Series,  # [str] category names
    ) -> _SanitizeLabelsOutput:
        """Remove rows with NaN labels and verify that the remaining labels are expected categories."""
        category_names = tuple(category_names)
        # Remove rows with NaN labels.
        # They are allowed, but not used in training.
        y = y[~y.isna()]  # type: ignore[reportAssignmentType]
        # Verify that the remaining labels are in the allowed set
        if not y.isin(category_names).all():
            raise ValueError(f"Labels should be in {category_names}")
        category_name_to_index = {name: i for i, name in enumerate(category_names)}
        y = y.map(category_name_to_index)
        number_of_labels_in_training = len(y)
        return _SanitizeLabelsOutput(
            y=y,
            number_of_labels_in_training=number_of_labels_in_training,
        )

    @rp.task
    def train(
        self,
        category_names: tuple[str, ...],
        x: pd.DataFrame,  # [float], column names become feature names
        y: pd.Series,  # [int], category indices
    ) -> _LRTrainOutput:
        """Train a logistic regression model.

        Samples (x) and labels (y) will be matched by index.  Unmatches samples/labels will not be
        used in training.
        """
        label_name = str(y.name)
        if label_name in x.columns:
            raise ValueError(
                f"Label column {label_name} should not be a column of the features dataframe"
            )
        # Join the features and labels.
        j = x.join(y, how="inner")
        number_of_samples_in_training = len(j)
        x = j.drop(label_name, axis=1)
        y = j[label_name]  # type: ignore[reportAssignmentType]
        lr = LR()
        lr.fit(X=x.to_numpy(), y=y.to_numpy())
        feature_names = tuple(x.columns)
        return _LRTrainOutput(
            LRModel(
                bare_model=lr,
                feature_names=feature_names,
                category_names=category_names,
            ),
            number_of_samples_in_training=number_of_samples_in_training,
        )

    @rp.pipeline
    def training_pipeline(self) -> TrainPl:
        """Train a binary logistic regression model.

        Samples not associated with labels or whose labels are NaN will be ignored.
        Non-binary labels will raise an error.
        """
        sanitize = self.get(apps.autoid(self.sanitize_labels))
        train = self.get(apps.autoid(self.train))
        return cast(
            TrainPl,
            self.combine(
                pipelines=(
                    sanitize,
                    train,
                ),
                dependencies=(sanitize >> train,),
            ),
        )

    @rp.task[PredictInputs, PredictOutputs]
    def prediction_pipeline(
        self,
        model: LRModel,
        x: pd.DataFrame,
    ) -> _LRPredictOutput:
        # Reorder the columns by the order in which they were used in training.
        x = x[list(model.feature_names)]  # type: ignore[reportAssignmentType]
        logits_np = model.bare_model.predict_log_proba(X=x.to_numpy())
        logits = pd.DataFrame(
            logits_np,
            index=x.index,
            columns=model.category_names,  # type: ignore[reportArgumentType]
        )
        return _LRPredictOutput(logits=logits)


class LRPipelineServices:
    TRAIN_PIPELINE = apps.autoid(LRPipelineContainer.training_pipeline)
    PREDICT_PIPELINE = apps.autoid(LRPipelineContainer.prediction_pipeline)
