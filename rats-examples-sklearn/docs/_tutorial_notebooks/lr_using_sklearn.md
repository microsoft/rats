```python
# type: ignore
# there are multiple typing issues in pandas and the iris dataset, easier to disable typing for
# this notebook
```


```python
from collections.abc import Sequence
from typing import NamedTuple

import pandas as pd
from sklearn.linear_model import LogisticRegression as LR

from rats import processors as rp
from rats.processors import typing as rpt
```

Let's build something a little more interesting - logistic regression using sklearn, with
safeguards using pandas dataframes.


First we'll create a `Model` class that will hold the bare sklearn LR model, but also the meta
information that verifies that a pandas dataframe can be used to predict with the model.


```python
class LRModel(NamedTuple):
    bare_model: LR
    feature_names: tuple[str, ...]
    category_names: tuple[str, ...]
```

Next, we'll build pipelines in a container class.
As before, we need to define NamedTuple classes for the output of each task.


```python
class _SanitizeLabelsOutput(NamedTuple):
    y: pd.Series  # [int], contegory indices from [0, NumCategories)
    number_of_labels_in_training: int


class _LRTrainOutput(NamedTuple):
    model: LRModel
    number_of_samples_in_training: int


class _LRPredictOutput(NamedTuple):
    logits: pd.DataFrame  # [float], columns are category names


class LRPipelineContainer(rp.PipelineContainer):
    @rp.task
    def sanitize_labels(
        self,
        category_names: Sequence[str],  # order will determine category index in output.
        y: pd.Series,  # [str] category names.
    ) -> _SanitizeLabelsOutput:
        """Remove rows with NaN labels and verify that the remaining labels are expected categories."""
        category_names = tuple(category_names)
        # Remove rows with NaN labels.
        # They are allowed, but not used in training.
        y = y[~y.isna()]
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
        y = j[label_name]
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
    def training_pipeline(self) -> rpt.UPipeline:
        """Train a binary logistic regression model.

        Samples not associated with labels or whose labels are NaN will be ignored.
        Non-binary labels will raise an error.
        """
        sanitize = self.sanitize_labels()
        train = self.train()
        return self.combine(
            pipelines=(
                sanitize,
                train,
            ),
            dependencies=(sanitize >> train,),
        )

    @rp.task
    def prediction_pipeline(
        self,
        model: LRModel,
        x: pd.DataFrame,
    ) -> _LRPredictOutput:
        # Reorder the columns by the order in which they were used in training.
        x = x[list(model.feature_names)]
        logits_np = model.bare_model.predict_log_proba(X=x.to_numpy())
        logits = pd.DataFrame(
            logits_np, index=x.index, columns=list(model.category_names)
        )
        return _LRPredictOutput(logits=logits)


lrpc = LRPipelineContainer()
app = rp.NotebookApp()
```


The training pipeline is composed of a `sanitize_labels` task followed by a `train` task.
Let's look at these sub-pipelines:


```python
sanitize_labels = lrpc.sanitize_labels()
app.display(sanitize_labels)
```



![png](lr_using_sklearn_files/lr_using_sklearn_8_0.png)




```python
train = lrpc.train()
app.display(train)
```



![png](lr_using_sklearn_files/lr_using_sklearn_9_0.png)



Look at the `training_pipeline` method and observe:

- The two sub-pipelines are created using by calling the reserpective methods. At this point, it
  does not matter that the sub-pipelines are tasks - any pipeline would work. It is important
  that the sub-pipelines are defined by methods of this container, because it ensures that they
  have distinct names.

- The `combine` method is used to combine the sub-pipelines into a another pipeline.  The
  argument `dependencies=(sanitize >> train,),` inspects the outputs of `sanitize` and the inputs
  of `train`, matches them by name, and creates edges between matches.  Here this means that the
  `y` output of `sanitize` will be connected to the `y` input of `train`.

- Inputs of any sub-pipeline that are not matches with outputs of another sub-pipeline will
  become inputs of the combined pipeline.  Here this means the `y` input of `sanitize`, and the
  `x` input of `train`, and the `category_names` input of both will become inputs of the combined
  pipeline.  The `category_names` input will flow to both `sanitize` and `train`, coupling them
  to always take the same value.  There are ways to change that behaviour, but more on that in
  other tutorials.

- Outputs of any sub-pipeline that are not matches with inputs of another sub-pipeline will
  become outputs of the combined pipeline.  There are ways to expose outputs of sub-pipelines
  that are matched to inputs of other sub-pipelines, but more on that in other tutorials.

Here's the combined training pipeline:


```python
training_pipeline = lrpc.training_pipeline()
print("Training pipeline input ports:", training_pipeline.inputs)
print("Training pipeline output ports:", training_pipeline.outputs)
app.display(training_pipeline)
```
_cell output_:
```output
Training pipeline input ports: InPorts(category_names=InPort[collections.abc.Sequence[str]], y=InPort[pandas.core.series.Series], x=InPort[pandas.core.frame.DataFrame])
Training pipeline output ports: OutPorts(number_of_labels_in_training=OutPort[int], model=OutPort[__main__.LRModel], number_of_samples_in_training=OutPort[int])
```


![png](lr_using_sklearn_files/lr_using_sklearn_11_1.png)



The prediction pipeline is a single task:


```python
prediction_pipeline = lrpc.prediction_pipeline()
print("Prediction pipeline input ports:", prediction_pipeline.inputs)
print("Prediction pipeline output ports:", prediction_pipeline.outputs)
app.display(prediction_pipeline)
```
_cell output_:
```output
Prediction pipeline input ports: InPorts(model=InPort[__main__.LRModel], x=InPort[pandas.core.frame.DataFrame])
Prediction pipeline output ports: OutPorts(logits=OutPort[pandas.core.frame.DataFrame])
```


![png](lr_using_sklearn_files/lr_using_sklearn_13_1.png)




To run the training pipeline we'll need a samples dataframe and a labels series.
We can then run the prediction pipeline with the trained model and a samples dataframe.
Let's use the Iris dataset, using category names rather than category indices for labels, and
splitting to train/test randomly.


```python
from sklearn import datasets

iris = datasets.load_iris()
category_names = tuple(iris["target_names"])

samples = pd.DataFrame(iris["data"], columns=iris["feature_names"])
labels = pd.Series(iris["target"], name="label").map(lambda i: category_names[i])
train_indices = samples.sample(frac=0.8).index
samples_train = samples.loc[train_indices]
labels_train = labels.loc[train_indices]
samples_test = samples.drop(train_indices)[
    iris["feature_names"][::-1]
]  # Reverse the columns
labels_test = labels.drop(train_indices)
```


```python
training_outputs = app.run(
    training_pipeline,
    inputs=dict(
        category_names=category_names,
        x=samples_train,
        y=labels_train,
    ),
)
```


```python
prediction_outputs_train = app.run(
    prediction_pipeline,
    inputs=dict(
        model=training_outputs["model"],
        x=samples_train,
    ),
)
```


```python
prediction_outputs_test = app.run(
    prediction_pipeline,
    inputs=dict(
        model=training_outputs["model"],
        x=samples_test,
    ),
)
```

Group logits by true label to see how the model is performing:


```python
prediction_outputs_train["logits"].join(labels_train).groupby("label").agg(
    ["mean", "std", "count"]
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead tr th {
        text-align: left;
    }

    .dataframe thead tr:last-of-type th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr>
      <th></th>
      <th colspan="3" halign="left">setosa</th>
      <th colspan="3" halign="left">versicolor</th>
      <th colspan="3" halign="left">virginica</th>
    </tr>
    <tr>
      <th></th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
    </tr>
    <tr>
      <th>label</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>setosa</th>
      <td>-0.024784</td>
      <td>0.012254</td>
      <td>44</td>
      <td>-3.830012</td>
      <td>0.503206</td>
      <td>44</td>
      <td>-16.085735</td>
      <td>0.993230</td>
      <td>44</td>
    </tr>
    <tr>
      <th>versicolor</th>
      <td>-4.437794</td>
      <td>1.343680</td>
      <td>37</td>
      <td>-0.212645</td>
      <td>0.204093</td>
      <td>37</td>
      <td>-2.533020</td>
      <td>1.345161</td>
      <td>37</td>
    </tr>
    <tr>
      <th>virginica</th>
      <td>-10.097900</td>
      <td>2.877340</td>
      <td>39</td>
      <td>-2.691922</td>
      <td>1.403706</td>
      <td>39</td>
      <td>-0.171744</td>
      <td>0.213766</td>
      <td>39</td>
    </tr>
  </tbody>
</table>
</div>




```python
prediction_outputs_test["logits"].join(labels_test).groupby("label").agg(
    ["mean", "std", "count"]
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead tr th {
        text-align: left;
    }

    .dataframe thead tr:last-of-type th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr>
      <th></th>
      <th colspan="3" halign="left">setosa</th>
      <th colspan="3" halign="left">versicolor</th>
      <th colspan="3" halign="left">virginica</th>
    </tr>
    <tr>
      <th></th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
      <th>mean</th>
      <th>std</th>
      <th>count</th>
    </tr>
    <tr>
      <th>label</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>setosa</th>
      <td>-0.031355</td>
      <td>0.007162</td>
      <td>6</td>
      <td>-3.498385</td>
      <td>0.213893</td>
      <td>6</td>
      <td>-15.448952</td>
      <td>0.625208</td>
      <td>6</td>
    </tr>
    <tr>
      <th>versicolor</th>
      <td>-4.030292</td>
      <td>1.248497</td>
      <td>13</td>
      <td>-0.133180</td>
      <td>0.090179</td>
      <td>13</td>
      <td>-3.150326</td>
      <td>1.414878</td>
      <td>13</td>
    </tr>
    <tr>
      <th>virginica</th>
      <td>-9.550154</td>
      <td>2.666712</td>
      <td>11</td>
      <td>-2.322399</td>
      <td>1.333171</td>
      <td>11</td>
      <td>-0.236352</td>
      <td>0.272456</td>
      <td>11</td>
    </tr>
  </tbody>
</table>
</div>




```python

```

Next, we'll build pipelines that incorporate pipelines defined in other containers.
