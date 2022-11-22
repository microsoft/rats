# Intermediate Tutorial

In the [beginners tutorial](beginners.md) we have seen how to construct `hello_world`, `diamond`
and `standardized_lr` pipelines.
In this tutorial we will dive deeper into some of the concepts we scratched and discuss more
complicated use cases.


## Defining Tasks

A *task* is a pipeline of a single node.
Creating a task requires specifying the pararameters needed for the *processor* class to be
initialized (such as configuration), dynamic input and output annotations, and compute
requirements.

A *task* has the following construct parameters:

* `processor_type` (`type`): a reference to the processor's class.
* `name` (`str`): \[optional\] name of the task. If missing, `processor_type.__name__` is used.
* `params_getter` (`oneml.processors.IGetParams`): \[optional\] a (serializable) *mapping* object
    whose keys & values are called to construct `processor_type` before executing it.
    Data dependencies will be grabbed automatically, but any other missing parameters for the
    constructor need to be specified here.
* `return_annotations` (`Mapping[str, type]`): \[optional\] an argument to override the *processors*
    original return annotation.
    This is useful when the number of outputs a processor returns varies between pipelines, and
    only known at build time, e.g., a data splitter for cross-validation.
* `compute_requirements` (`oneml.processors.PComputeReqs`): \[optional\] stores information about
    the resources the *processor* needs to run, e.g., CPUs, GPUs, memory, etc.


### Passing Constructor Parameters

The following example implements a data loader.
In this example the data loader will get its constructor parameters from an in-memmory immutable
dictionary, i.e., `frozendict`.
Other mechanims are also supported, e.g., by instantiating objects from configuration.

```python
from typing import Any, Mapping, TypedDict
from oneml.processors import frozendict, PipelineClient

LoadDataOut = TypedDict("LoadDataOut", {"data": Any})

class LoadData:
    def __init__(self, storage: Mapping[str, float]):
        self._storage = storage

    def process(self, key: str) -> LoadDataOut:
        return LoadDataOut(data=self._storage["key"])

storage = frozendict({"X_train": 5, "X_eval": 1, "Y_train": 0, "Y_eval": 1})
load_data = PipelineClient.task(processor_type=LoadData, name="load_data", params_getter=storage)
```

Here, `frozendict` is an immutable and serializable *mapping* object.
These properties, i.e., immutability, serializability and the *mapping* interface consititute the
requirements for providing configuration into *processors*.
Overall, `params_getter` follows the [`IGetParams` interface](advanced.md#defining-params_getters).

### Dynamic Annotations

Consider the following *processor*:

```python
from typing import Any, Mapping

class Identity:
    def process(self, **kwargs) -> Mapping[str, Any]:
        return kwargs
```

It is a simple processor that returns all parameters it receives.
It is a *processor* because it implements the *process* method and returns a `Mapping` with
annotated variables.
However, `Identity` does not specify the name of the variables that it expects or returns, and we
cannot know them a priori.

That is the reason why `oneml.processors.PipelineClient.task` accepts `input_annotation` and 
`return_annotation` parameters.
For most *processors* these arguments will be unncessary, but if we provide them, they will
override the class's input or return signatures, respectively.

For example,

```python
from oneml.processors import PipelineClient

io_annotation = {"foo": str, "boo": bool, "hey": int}
PipelineClient.task(Identity, input_annotation=io_annotation, return_annotation=io_annotation)
```

> **NOTE:**
> 
> Passing `return_annotation=None` (default) will not override the *processor's* return signature.
Only if the return signature of a processor AND if `return_annotation=None`, will the framework
assume that the *processor* return type is actually `None`.
Same applies to `input_annotation=None`.


## Combining Pipelines

We will explain how to deal with variable name reuse (collections) and how to expose or rewire
input and output names when composing pipelines.

### Parameter Collections

In [begginer's tutorial](beginners.md) we wrote simple pipelines that connect tasks together
defining their dependencies.
However, all *processors*' inputs and outputs had unique names.
This was an artificial requirement to simplify the exposition.

Consider now the following `standardization` pipeline:
```python
from typing import TypedDict
from oneml.processors import PipelineClient

StandardizeTrainOut = TypedDict("StandardizeTrainOut", {"mean": float, "scale": float, "Z": float})
StandardizeEvalOut = TypedDict("StandardizeEvalOut", {"Z": float})

class StandardizeTrain(self):
    def process(X: float) -> StandardizeTrainOut:
        ...

class StandardizeEval(self):
    def __init__(self, mean: float, scale: float) -> None:
        ...

    def process(X: float) -> StandardizeEvalOut:
        ...

stz_train = PipelineClient.task(StandardizeTrain, name="stz_train")
stz_eval = PipelineClient.task(StandardizeEval, name="stz_eval")

standardization = PipelineClient.combine(
    stz_train, stz_eval
    name="standardization",
    dependencies=(
        stz_eval.inputs.mean << stz_train.outputs.mean,
        stz_eval.inputs.scale << stz_train.outputs.scale,
    )
)
```

What is different from before is that `StandardizeTrain` and `StandardizeEval` inputs and outputs
are `X`, and `Z`, rather than `X_train`, `Z_train` or `X_eval`, `Z_eval`, respectively.
Both *processors* share the same input and output variable names.

When we combine `stz_train` and `stz_eval`, inputs and outputs are extracted and made accessible
via their variable name, as before:
```python
standardization.inputs.X  # InCollection object
standardization.outputs.Z  # OutCollection object
```

However, both `standardization.inputs.X` and `standardization.outputs.Z` are now representing a
two inputs and two outputs, one for each *processor*, rather than a unique one.
The individual parameters are still accessible via
```python
standardization.inputs.X.stz_train  # InParameter objects
standardization.inputs.X.stz_eval
standardization.outputs.Z.stz_train  # OutParameter objects
standardization.outputs.Z.stz_eval
```

Accessing `inputs` and `outputs` attribute of a pipeline returns a mapping of the parameters it
exposes;
accessing a variable returns a collection;
accessing an entry within a collection, returns a single input or output parameter.

These are the returned types from the nested mappings, accessible via dot notation:

| `Pipeline`        | `InPipeline`     | `InCollection`  | `InParameter`  |
|-------------------|------------------|-----------------|----------------|
| `standardization` | `.inputs`        | `.X`            | `.stz_train`   |
| `standardization` | `.inputs`        | `.X`            | `.stz_eval`    |
|                   |                  |                 |                |

| `Pipeline`        | `OutPipeline`    | `OutCollection` | `OutParameter` |
|-------------------|------------------|-----------------|----------------|
| `standardization` | `.outputs`       | `.Z`            | `.stz_train`   |
| `standardization` | `.outputs`       | `.Z`            | `.stz_eval`    |
|                   |                  |                 |                |   


### Operations with Parameters and Collections

Consider now the second pipeline example based on logistic regression with variable renames, e.g.,
`X_train`, `X_eval` into `X`, and similar for `Y` and `Z`.

```python
LogisticRegressionTrainOut = TypedDict("LogisticRegressionTrainOut", {"model": tuple[float], "Z": float})
LogisticRegressionEvalOut = TypedDict("LogisticRegressionEvalOut", {"Z": float, "probs": float})

class LogisticRegressionTrain(self):
    def process(X: float, Y: float) -> LogisticRegressionTrainOut:
        ...

class LogisticRegressionEval(self):
    def __init__(self, model: tuple[float, ...]) -> None:
        ...

    def process(X: float, Y: float) -> LogisticRegressionEvalOut:
        ...

lr_train = PipelineClient.task(ModelTrain, name="lr_train")
lr_eval = PipelineClient.task(ModelEval, name="lr_eval")

logistic_regression = PipelineClient.combine(
    lr_train, lr_eval
    name="logistic_regression",
    dependencies=(lr_eval.inputs.model << lr_train.outputs.model,)
)
```

#### `InParameter` & `OutParameter`:

**Left and right shift operations:**

You can create dependencies using the left and right shift operators:

```python
standardization.outputs.Z.stz_train >> logistic_regression.inputs.X.lr_train
logistic_regression.inputs.X.lr_eval << standardization.outputs.Z.stz_eval
```

These operators return a dependency wrapped in a tuple (for compatibility with collections), which
can be passed as part of dependencies when combining pipelines.

By default, the collection entry, e.g., `Z.stz_train` or `X.lr_eval` in the example, are set to the
node's name for tasks, and to the pipeline's name when combining tasks.
These reference names can be changed, as we show below.

#### `InCollection` & `OutCollection`:

**Rename:** Collections can rename entries.

```python
lr_incollection = logistic_regression.inputs.X.rename({"lr_train": "train", "lr_eval": "eval"})
stz_outcollection = standardization.outputs.Z.rename({"stz_train": "train", "stz_eval": "eval"})
```

The `rename` method accepts a `Mapping[str, str]` with `{"current_name": "new_name"}` format.
Note that collections are immutable, so a new collection is returned instead.
You can use the returned collections to operate.

**Left and right shift operations:**

Similar to single parameters, you can create dependencies using the left and right shift operators.

```python
lr_incollection.X << stz_outcollection.Z  # equivalent: stz_outcollection.Z >> lr_incollection.X
```

Both collections need to have same number of entries, and entry names need to be matched, i.e.,
`Z.train` with `X.train` and `Z.eval` with `X.eval`, respectively.
The operation returns a tuple of dependencies the size of the collections.
In this case, it returns two dependencies, one for `train` and one for `eval`.

We can use these mechansims to combine these pipelines together:
```python
stz_lr = PipelineBuileder(
    standardization, logistic_regression,
    name="stz_lr",
    dependencies=(lr_incollection.X << stz_outcollection.Z,)  # two dependencies
)
```

Alternatively, collections from one entry to many are also permitted, and names need not to match.

```python
class Report:
    def process(probs: float) -> None:
        ...

report1 = PipelineBuilder.task(Report, name="report1")
report2 = PipelineBuilder.task(Report, name="report2")
reports = PipelineBuileder.combine(report1, report2, name="reports")

reports.inputs.probs  # InCollection of two entries
lr_eval.outputs.probs  # InCollection of single entry

reports.inputs.probs << lr_eval.outputs.probs  # ok; returns two dependencies
```

This syntax is particularly useful to broadcast a single result to multiple entries.


## Estimators (Recommended Pattern)

We have shown a mechanism to create tasks, combine, rename inputs & outputs, and combine the
resulting pipelines:

1. Instantiate tasks, i.e., `stz_train`, `stz_eval`, `lr_train`, `lr_eval`.
2. Combine tasks, i.e., `standardization` and `logistic_regression`.
3. Rename entries, i.e., `stz_train`, `lr_train` to `train` and `stz_eval`, `lr_eval` to `eval`.
4. Combine pipelines, i.e., `standartization` and `logistic_regression` to `stz_lr`.

This pattern can be simplified with estimators:

```python
from oneml.processors import Estimator

# Instantiate tasks
stz_train = PipelineClient.task(StandardizeTrain)
stz_eval = PipelineClient.task(StandardizeEval)
lr_train = PipelineClient.task(ModelTrain)
lr_eval = PipelineClient.task(ModelEval)

# Instantiate estimators
standardization = Estimator(
    stz_train, stz_eval,
    name="standardization",
    shared_params=(
        stz_eval.inputs.mean << stz_train.outputs.mean,
        stz_eval.inputs.scale << stz_train.outputs.scale,
    )
)
logistic_regression = Estimator(
    lr_train, lr_eval,
    name="logistic_regression",
    shared_params=(
        lr_eval.inputs.model << lr_train.outputs.model,
    )
)

# Combine estimators
stz_lr = PipelineBuilder.combine(
    standardization, logistic_regression
    name="stz_lr",
    dependencies=(logistic_regression.inputs.X << standardization.outputs.Z,)
)
```

The main advantage for using estimators is that collections are built in a way such that they are
compatible to combine and operate with together.
This abstracts the number of entries that a collection encapsulates.
