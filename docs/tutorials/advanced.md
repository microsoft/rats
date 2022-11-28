# Advanced Tutorial

In this tutorial we will dive deeper into concepts, and will allow you to reconfigure pipelines 
and build your own meta-pipelines.


## Inputs & Outputs of Pipelines

In the [intermediate tutorial](intermediate.md) we explained how collections of parameters are
created and some of the operations they support, e.g., left/right shift and rename.
Collections simplify operating with compatible pipelines that expose equal-named variables, such as
`X` for input features, `Z` for output features, for train and eval operations, respectively.

Collections are convenient for grouping equal-named parameters, but they were created automatically
and users may require more granular control, or make want to make more arbitrary groupings to
define such collections.
This is what the `inputs` and `outputs` arguments of `PipelineBuilder.combine` are for.

`PipelineBuilder.combine` has the following parameter specification:

* `*pipelines` (`Pipeline`): a sequence of `Pipeline`s to combine; must have different names.
* `name` (`str`): name of the returned, combined pipeline.
* `dependencies` (`Iterable[Sequence[Dependency]]`): \[optional\] the dependencies between the
    pipelines to combine, e.g., `(logistic_regression.inputs.X << standardization.outputs.Z,)`.
* `inputs` (`UserInput | None`): input names that the returned pipeline exposes; `UserInput`
    is a `Mapping` in `{variable.collection_entry: InParameter | InCollection}` format.
* `outputs` (`UserOutput | None`): ouput names that the returned pipeline exposes; `UserOutput`
    is a `Mapping` in `{variable.collection_entry: OutParameter | OutCollection}` format.


### Requirements of `UserInput` and `UserOutput`

The full specification of `inputs` and `outputs` has several requirements.
Let's consider the following example for illustrative purposes:

```python
from oneml.processors import PipelineBuilder
from oneml.processors.ml import Estimator

standardization = Estimator(
    name="standardization",
    train_pl=standardize_train,
    eval_pl=standardize_eval,
    shared_params=(
        standardize_eval.inputs.mean << standardize_train.outputs.mean,
        standardize_eval.inputs.scale << standardize_train.outputs.scale,
    ),
)

logistic_regression = Estimator(
    name="logistic_regression",
    train_pl=model_train,
    eval_pl=model_eval,
    shared_params=(model_eval.inputs.model << model_train.outputs.model,),
)

stz_lr = PipelineBuilder.combine(
    standardization,
    logistic_regression,
    name="stz_lr",
    dependencies=(logistic_regression.inputs.X << standardization.outputs.Z,),
    inputs={"X": standardization.inputs.X, "Y": logistic_regression.inputs.Y},
    outputs={
        "mean": standardization.outputs.mean.train,
        "scale": standardization.outputs.scale,
        "model": logistic_regression.outputs.model.train,
        "probs.train": logistic_regression.outputs.probs.train,
        "probs.eval": logistic_regression.outputs.probs.eval,
        "acc": logistic_regression.outputs.acc,
    },
)
```

* `.collection_entry` is optional if the value assignment is an `InParameter` / `OutParameter` or
    an `InCollection` / `OutCollection` of length one (single entry); 

```python
outputs = {"mean": standardization.outputs.mean.train, "scale": standardization.outputs.scale}
```

In the above example `standardization.outputs.mean.train` is an `OutParameter`, and 
`standardization.outputs.scale` is an `OutCollection` of length one.
Therefore the dot notation becomes optional;

* `.collection_entry` must be empty if the value assignment is an `InCollection` / `OutCollection`
    of length greather than one.

```python
inputs = {"X": standardization.inputs.X, "Y": logistic_regression.inputs.Y}
```

In the above example both `standardization.inputs.X` and `logistic_regression.inputs.Y` are input
collections of length two, with collection entries `train` and `eval` in both cases.

On the other hand, this would be equivalent to the above:
```python
inputs = {
    "X.train": standardization.inputs.X.train,
    "X.eval": standardization.inputs.X.eval,
    "Y.train": logistic_regression.inputs.Y.train,
    "Y.eval": logistic_regression.inputs.Y.eval
}
```

* All *inputs* (all collection entries from all variables) to the pipeline must be specified:

```python

inputs = {
    "X.train": standardization.inputs.X.train,
    # "X.eval": standardization.inputs.X.eval,
    "Y.train": logistic_regression.inputs.Y.train,
    "Y.eval": logistic_regression.inputs.Y.eval
}  # missing one entry will raise an error
```

* Exposing any `outputs` is optional:

```python
outputs = {}  # ok; no outputs are exposed
outputs = {
    "model.train": logistic_regression.outputs.model.train,  # OutParameter assignment
    "probs": logistic_regression.outputs.probs,  # OutCollection of length 2
    "acc": logistic_regression.outputs.acc,  # OutCollection of length 1
}  # ok; `standardization.outputs.mean` and `standardization.outputs.scale` are NOT exposed
```

* Any reassignment of `variable` and/or `.collection_entry` names are valid for re-specifying the
inputs and/or outputs of pipelines:

```python
outputs = {
    "A.mean": standardization.outputs.mean.train,
    "A.scale": standardization.outputs.scale,
    "A.model": logistic_regression.outputs.model.train,
    "A.probs_train": logistic_regression.outputs.probs.train,
    "A.probs_eval": logistic_regression.outputs.probs.eval,
    "acc": logistic_regression.outputs.acc,
}
```

In the above example we are combining the outputs of several pipelines into `A` by specifying
five collection entries with new and/or old entry names.
The above combined `UserOutput` would expose two variables, i.e., `A` and `acc`.

* `UserInput` or `UserOutput` can have at most single dot in the *mapping* keys.
An error will be raised otherwise.


### Defaults for `UserInput` and `UserOutput`

If you leave `inputs` and `outputs` of `PipelineBuilder.combine` unspecified or set to `None`, a
default specificiation will be made automatically:

* All `inputs` or `outputs` from pipelines to combine will be merged, after subtracting any input
or output specified in the `dependencies` argument`.

For example,
```
stz_lr = PipelineBuilder.combine(
    standardization,
    logistic_regression,
    name="stz_lr",
    dependencies=(logistic_regression.inputs.X << standardization.outputs.Z,),
    inputs=None,
    outputs=None,
)
```

Leaving `inputs=None` is equivalent to
`inputs={"X": standardization.inputs.X, "Y": logistic_regression.inputs.Y}`.
The reason is because `logistic_regression.inputs.X` is specified as a dependency, and is removed
from the default merge.

Leaving `outputs=None` is equivalent to
```python
outputs={
    "mean": standardization.outputs.mean,
    "scale": standardization.outputs.scale,
    "model": logistic_regression.outputs.model,
    "probs": logistic_regression.outputs.probs,
    "acc": logistic_regression.outputs.acc,}
```
because only `standardization.outputs.Z` is specified in the dependencies and, therefore, removed.

> **NOTE:**
> 
> Combinging pipelines with `Estimator` exposes all outputs from both pipelines.
That is why `standardization` exposes `mean` and `scale`, and why `logistic_regression` exposes
`model`, even though they are specified as dependencies.


## Pipelines

A `Pipeline` is a (frozen) dataclass with the following attributes:

* `name` (`str`): of the pipeline; used as the default value for collection entries; useful to
    distinguiss pipelines when combining.
* `dag` (`oneml.processors._dag.DAG`): graph representation of nodes, dependencies and properties
    of processors.
* `inputs` (`oneml.processors.PipelineInput`): exposure of inputs of a pipeline, as explained in
    the [intermediate tutorial](intermediate.md#parameter-collections)
* `outputs` (`oneml.processors.PipelineOutput`): exposure of outputs of a pipeline, as explained in
    the [intermediate tutorial](intermediate.md#parameter-collections)

`Pipeline`s should not be instantiated directly.
Instead, `Pipeline`s should be created by creating `Task`s, combining other `Pipeline`s, or via
wrappers that output the desired `dag` structure, e.g., *cross-validation*.

In the rest of this tutorial we will explain how to write the mechanisms that operate with
`Pipeline`s to return new `Pipeline`s.


## Meta-Pipelines

In the [intermediate tutorial](intermediate.md) we explained the operations that can be performed
with `InParameter` / `OutParameter` and `InCollection` / `OutCollection`.

Let's now discuss operations with `PipelineInput` and `PipelineOutput`.
These operations will be useful to construct the classes that operate on top of pipelines and
return new pipelines (like `oneml.processor.ml.Estimator`).

### Operations with `PipelineInput` & `PipelineOutput`:

* You can subtract variables, single parameters, or collection of parameters:
```python
new_inputs = my_pipeline.inputs - ("X",)
new_inputs = my_pipeline.inputs - (my_pipeline.inputs.X,)
new_inputs = my_pipeline.inputs - (my_pipeline.inputs.X.train,)
```

All of the above are equivalent if `X` is a collection of length one.
The syntax requires subtracting an `Iterable` (like `tuple`, `list`, `set`, etc.).
If what you are trying to subtract does not exist, no error will be issued.

* You can merge pipeline inputs, or outputs:
```python
standardization.inputs | logistic_regression.inputs
```

Duplicates of the form `variable.collection_entry` are not permitted when merging and an error
will be raised if they occur.

* You can rename pipeline inputs, or outputs, similar to
[collections](intermediate.md#incollection--outcollection): 

```python
new_inputs = my_pipeline.inputs.rename({"lr_train": "train", "lr_eval": "eval"})
new_outputs = my_pipeline.inputs.rename({"Z": "Z_train", "acc": "acc_eval"})
```

Rename happens for all collection entries in all variables.
The specification is `Mapping[str, str]` where keys specify current names, and values new names.

* You can `decorate` a pipeline, i.e., wrap a pipeline under another name:
```python
new_pipeline = my_pipeline.decorate("p")
```

This is useful when combining pipelines of the same type that need to be unique.
Consider for example the following (dummy) example with some report generators:

```python
class Report:
    def process(probs: float) -> None:
        ...

report = PipelineBuilder.task(Report)
r1 = report.decorate("r1")
r2 = report.decorate("r2")
reports = PipelineBuileder.combine(
    r1, r2,
    name="reports",
    dependencies=(
        one_pipeline.outputs.probs >> r1.inputs.probs,
        two_pipeline.outputs.probs >> r2.inputs.probs, 
    )
)
```

### `Estimator` Example:

We can create the `Estimator` operator using the above operations:

```python
@dataclass(frozen=True, init=False)
class Estimator(Pipeline):
    def __init__(
        self,
        name: str,
        train_pl: Pipeline,
        eval_pl: Pipeline,
        shared_params: Iterable[Sequence[Dependency]] = ((),),
    ) -> None:
        # skip validation of arguments

        train_pl = train_pl.rename({train_pl.name: "train"}).decorate(name="train")
        eval_pl = eval_pl.rename({eval_pl.name: "eval"}).decorate(name="eval")
        dependencies = (dp.decorate("eval", "train") for dp in chain.from_iterable(shared_params))
        outputs = train_pl.outputs | eval_pl.outputs  # estimators expose shared parameters
        pl = PipelineBuilder.combine(
            train_pl,
            eval_pl,
            name=name,
            outputs=outputs,
            dependencies=(tuple(dependencies),),
        )
        super().__init__(name, pl.dag, pl.inputs, pl.outputs)  # calls the Pipeline constructor
```

A few clarifications:

1. We made `Estimator` a (frozen) dataclass extending `Pipeline`. This is because we consider
`Estimator` a concept and wanted to give it an entity, but this does not need to be so.

2. Arguments include a `train` and `eval` pipelines, estimator's name, and dependencies.

3. The first step is to try to rename the collection entries: any entry with the pipeline's name is
renamed into `train` and `eval`, respectively. This is because `Task`s use the task name as default
for entry names.

4. We decorate the `train` and `eval` pipelines before merging. This will ensure the combinantion
is valid.

5. Outputs are specified by merging the outputs of the `train` and `eval` pipelines, before
subtracting the specified dependencies.

6. Inputs are merged by subtracting the specified dependencies, default behavior.

7. Pipelines are combined, and a new `Pipeline` returned.
