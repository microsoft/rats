# Intermediate Tutorial

This tutorial is also available in notebook form.  See [Tutorial Notebooks](notebooks.md).

In the [beginners tutorial](tutorial_beginners.md) we have seen how to construct `hello_world`, `diamond`
and `standardized_lr` pipelines.
In this tutorial we will dive deeper into some of the concepts we touched upon and discuss more
complicated use cases.

#### Table of Contents

- [Defining Tasks](#defining-tasks)
  - [Constructor Parameters](#constructor-parameters)
  - [Dynamic Annotations](#dynamic-annotations)
  - [IOManagers and Serializers](#iomanagers-and-serializers)
- [Combining Pipelines](#combining-pipelines)
  - [Parameter Entries](#parameter-entries)
  - [Parameter Collections](#parameter-collections)
  - [Parameter Types](#parameter-types)
  - [Defaults for `UserInput` and `UserOutput`](#defaults-for-userinput-and-useroutput)
- [TrainAndEval](#trainandeval)

## Defining Tasks

A *task* is a pipeline of a single node.
Creating a task requires specifying the pararameters needed for the *processor* to be
initialized, i.e., configuration, dynamic input and output annotations, and compute
requirements.
A *task* has the following construct parameters:

- `processor_type` (`type[oneml.processors.IProcess]`): a reference to the processor's class.
- `name` (`str`): \[optional\] name of the task. If missing, `processor_type.__name__` is used.
- `config` (`Mapping[str, Any]`): \[optional\] A mapping from (a subset of) the the processor's
    constructor parameters to values.  The values need to be serializable.
- `services` (`Mapping[str, oneml.pipelines.session.ServiceId[Any]]`): \[optional\] A mapping from
    (a subset of) the the processor's constructor parameters to service ids.  See
    [Services](tutorial_advanced.md#services).
- `input_annotation` (`Mapping[str, type]`): \[optional\] dynamic inputs for variable keyword
    parameter, e.g., `**kwargs`; required if *processor* specifies
    [var keyword](https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind)
    parameters.
- `return_annotation` (`Mapping[str, type]`): \[optional\] dynamic outputs; overrides the
    *processors* return annotation. Useful when the number of outputs a processor returns varies
    between pipelines, and only known at build time, e.g., a data splitter for cross-validation.
- `compute_requirements` (`oneml.processors.PComputeReqs`): \[optional\] \[for future use\] stores
    information about the resources the *processor* needs to run, e.g., CPUs, GPUs, memory, etc.

### Task execution

When the task is executed it performs the following:

- collect input values from upstream nodes.
- collect constructor parameters from `config`, `services` and inputs (see
    [Constructor Parameters](#constructor-parameters)).
- construct a processor object by calling the constructor of `processor_type` with the collected
    constructor parameters it collected.
- call the process method of the processor object, passing the rest of the inputs.
- publish the outputs of the process method as the task outputs.

### Constructor Parameters

To construct a processor object, the task needs to provide a value for each parameter of the
constuctor of `processor_type`.

For each such parameter, the value will be provided in one of the following three ways:

- If the parameter appears in `config` its value is take from there.
- If the parameter appears in `services`, it is mapped to a service id.  The framework will look
    for the appropriate service provider in the services registry of the executing environment, and
    call it to provide a service object.  That service object will be the value for the parameter.
- If the parameter does not appear in `config` nor in `services`, it is assumed to be an input to
    the `task`.  Its value will be taken from those inputs.

The following example implements saving a pandas dataframe to a local csv file:

```python
from pathlib import Path
import pandas as pd
from typing import NamedTuple
from oneml.processors import PipelineBuilder, display_dag

class SavePandasOut(NamedTuple):
    file_path: str

class SavePandas:
    def __init__(self, output_folder: Path, file_name: str):
        self._file_path = output_folder / file_name

    def process(self, df: pd.DataFrame) -> SavePandasOut:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self._file_path)
        return SavePandasOut(file_path=self._file_path)
```

We can provide the constuctor arguments when we build the task, like this:

```python
save_pandas_1 = PipelineBuilder.task(
    processor_type=SavePandas,
    config=dict(
        output_folder=Path(".tmp"),
        file_name="a.csv",
    ),
)

display_dag(save_pandas_1)
```

Or, we can ommit some of them it and they will become an inputs the the task:

```python
save_pandas_2 = PipelineBuilder.task(
    processor_type=SavePandas,
    config=dict(
        file_name="a.csv",
    ),
)

display_dag(save_pandas_2)
```

Finally, we can ask the framework to provide a service object as the value of a contructor
argument, like this:

```python
from oneml.habitats import OnemlHabitatsServices

save_pandas_3 = PipelineBuilder.task(
    processor_type=SavePandas,
    config=dict(
        file_name="a.csv",
    ),
    services=dict(
        output_folder=OnemlHabitatsServices.TMP_PATH,
    ),
)

display_dag(save_pandas_3)
```

Let's take a minute to execute these three pipelines.

We'll need a pipeline runner factory:

```python
from oneml.processors import OnemlProcessorsServices

pipeline_runner_factory = oneml_service_provider.get_service(
    OnemlProcessorsServices.PIPELINE_RUNNER_FACTORY)
```

And we'll need to provide a dataframe as input:

```python
df = pd.DataFrame(dict(A=[10,20,30], B=["a","b","c"]))
```

Executing the first version, providing `df`, and then inspecting the `file_path` output:

```python
runner = pipeline_runner_factory(save_pandas_1)
outputs = runner(
    dict(
        df=df
    )
)
print(outputs.file_path)
```

Verifying the output file:

```python
with outputs.file_path.open() as r:
    print(r.read())
```

Executing the second version.  Recall that it requires `output_folder` as input.

```python
runner = pipeline_runner_factory(save_pandas_2)
outputs = runner(dict(df=df, output_folder=Path(".my_output_folder/")))
print(outputs.file_path)
with outputs.file_path.open() as r:
    print(r.read())
```

Executing the third version.  Here we trust `OnemlHabitatsServices.TMP_PATH` to define the output
folder for us.

```python
runner = pipeline_runner_factory(save_pandas_3)
outputs = runner(dict(df=df))
print(outputs.file_path)
with outputs.file_path.open() as r:
    print(r.read())
```

### Dynamic Annotations

Consider the following *processor*:

```python
from typing import Any, Mapping


class Identity:
    def process(self, **kwargs) -> Mapping[str, Any]:
        return kwargs
```

It is a simple processor that returns all parameters it receives.

It implements the *process* method and returns a `Mapping` with annotated variables.
However, `Identity` does not specify the name of the variables that it expects or returns, and we
do not know them a priori.

They do need to be specified at pipeline construction time, and that is the reason why
`oneml.processors.Task` accepts `input_annotation` and `return_annotation` parameters.

For most *processors* these arguments will be unncessary, but if we provide them, they will
override the class's input or output signatures, respectively.

For example:

```python
from oneml.processors import PipelineBuilder

io_annotation = {"foo": str, "boo": bool, "bee": int}
t = PipelineBuilder.task(Identity, input_annotation=io_annotation, return_annotation=io_annotation)
```

> :notebook: **Note**:
Passing `return_annotation=None` (default) will not override the *processor's* return signature.
Only if the return signature of a processor AND if `return_annotation=None`, will the framework
assume that the *processor* return type is actually `None`.
Same applies to `input_annotation=None`.

## Combining Pipelines

We will further explain how to combine pipelines, handle name conflicts, and expose inputs and
outputs.

### PipelineBuilder.combine

The exact parameter signature of `PipelineBuilder.combine` is the following:

- `pipelines` (`Pipeline`): a sequence of `Pipeline`s to combine; must have different names.
- `name` (`str`): name of the returned, combined pipeline.
- `dependencies` (`Iterable[Sequence[oneml.ux.Dependency]]`): dependencies between the pipelines to
    combine, e.g., `stz_eval.inputs.mean << stz_train.outputs.mean`.
- `inputs` (`oneml.ux.UserInput | None`): mapping names of inputs and in_collectins of the
  pipelines to combine.
- `outputs` (`oneml.ux.UserOutput | None`): mapping names of outputs and out_collectins of the
  pipelines to combine.

Arguments `inputs` and `outputs` are optional and help configure the exposed input and output
variables of the combined pipeline.

The exact definitions are the following:

- `UserInput = Mapping[str, oneml.ux.InEntry | oneml.ux.Inputs]`
- `UserOutput = Mapping[str, oneml.ux.OutEntry | oneml.ux.Outputs]`

Default behavior for `inputs` and `outputs` set to None is explained in the
[section](#defaults-for-userinput-and-useroutput) below.

> :notebook: **Note:**
Dependencies are not expected to be created manually, but through the `<<` operator syntax.

Consider the following `standardization` example:

```python
from typing import NamedTuple
from oneml.processors import PipelineBuilder

class StandardizeTrainOut(NamedTuple):
    mean: float
    scale: float
    Z: float

class StandardizeTrain:
    def process(X: float) -> StandardizeTrainOut:
        ...

class StandardizeEvalOut(NamedTuple):
    Z: float

class StandardizeEval:
    def __init__(self, mean: float, scale: float) -> None:
        ...

    def process(X: float) -> StandardizeEvalOut:
        ...


stz_train = PipelineBuilder.task(StandardizeTrain)
stz_eval = PipelineBuilder.task(StandardizeEval)

standardization = PipelineBuilder.combine(
    pipelines=[stz_train, stz_eval],
    name="standardization",
    dependencies=(
        stz_eval.inputs.mean << stz_train.outputs.mean,
        stz_eval.inputs.scale << stz_train.outputs.scale,
    ),
    inputs={"X.train": stz_train.inputs.X, "X.eval": stz_eval.inputs.X},
    outputs={
        "mean": stz_train.outputs.mean,
        "scale": stz_train.outputs.scale,
        "Z.train": stz_train.outputs.Z,
        "Z.eval": stz_eval.outputs.Z,
    },
)

display_dag(standardization)
```

Let's unwrap the example below.

### Parameter Entries

We have specified dependencies between the `stz_train` and `stz_eval` using the `<<` operator:

```python
stz_eval.inputs.mean << stz_train.outputs.mean,
stz_eval.inputs.scale << stz_train.outputs.scale,
```

We access single inputs and outputs of the pipelines via the `inputs` and `outputs` attributes.
This happens with `stz_eval.inputs.mean` and `stz_train.outputs.mean`, for example
In [begginer's tutorial](tutorial_beginners.md) we saw another example:

```python
stz_lr_dependencies = (
    logistic_regression.inputs.X_train << standardization.outputs.Z_train,
    logistic_regression.inputs.X_eval << standardization.outputs.Z_eval,
)
```

> :notebook: **Note**:
In these examples *processors*' inputs and outputs had unique names.
If the variable parameters don't have unique names, we can expose them as collections of
parameters, as explained in the next section.

### Parameter Collections

Pipelines `stz_train` and `stz_eval` both expose `X` and `Z` variable names so we needed to
specify how `X` and `Z` are combined together.
In the `PipelineBuilder.combine` call we specified:

```python
inputs={"X.train": stz_train.inputs.X, "X.eval": stz_eval.inputs.X},
outputs={"Z.train": stz_train.outputs.Z, "Z.eval": stz_eval.outputs.Z}
```

The combined pipeline will expose variables as collections of parameters:

```python
standardization.in_collections.X  # Inputs object
standardization.out_collections.Z  # Outputs object
```

Both `standardization.in_collections.X` and `standardization.out_collections.Z` gather two inputs
and two outputs entries, respectively.
The individual entries are accessible via:

```python
standardization.in_collections.X.train  # InEntry objects
standardization.in_collections.X.eval
standardization.out_collections.Z.train  # OutEntry objects
standardization.out_collections.Z.eval
```

The usefulness of collections is that we can group parameters together and create dependencies.
Here another example with `logistic_regression`:

```python
from typing import NamedTuple
from oneml.processors import PipelineBuilder

class LogisticRegressionTrainOut(NamedTuple):
    model: tuple[float]
    Z: float

class LogisticRegressionTrain:
    def process(X: float, Y: float) -> LogisticRegressionTrainOut:
        ...

class LogisticRegressionEvalOut(NamedTuple):
    Z: float
    probs: float

class LogisticRegressionEval:
    def __init__(self, model: tuple[float, ...]) -> None:
        ...

    def process(X: float, Y: float) -> LogisticRegressionEvalOut:
        ...


lr_train = PipelineBuilder.task(LogisticRegressionTrain, name="lr_train")
lr_eval = PipelineBuilder.task(LogisticRegressionEval, name="lr_eval")

logistic_regression = PipelineBuilder.combine(
    pipelines=[lr_train, lr_eval],
    name="logistic_regression",
    dependencies=(lr_eval.inputs.model << lr_train.outputs.model,),
    inputs={
        "X.train": lr_train.inputs.X,
        "X.eval": lr_eval.inputs.X,
        "Y.train": lr_train.inputs.Y,
        "Y.eval": lr_eval.inputs.Y,
    },
    outputs={
        "Z.train": lr_train.outputs.Z,
        "Z.eval": lr_eval.outputs.Z,
        "model": lr_train.outputs.model,
        "probs": lr_eval.outputs.probs,
    },
)

display_dag(logistic_regression)
```

The inputs and outputs automatically formed after combining `lr_train` and `lr_eval` into
`logistic_regression` pipeline are:

```python
logistic_regression.outputs.probs  # OutEntry object

logistic_regression.in_collections.X  # Inputs objects
logistic_regression.in_collections.Y
logistic_regression.out_collections.Z  # Outputs object

logistic_regression.in_collections.X.train  # InEntry objects
logistic_regression.in_collections.X.eval
logistic_regression.in_collections.Y.train
logistic_regression.in_collections.Y.eval
logistic_regression.out_collections.Z.train  # OutEntry objects
logistic_regression.out_collections.Z.eval
```

Finally, we can combine `standardization` and `logistic_regression` together:

```python
stz_lr = PipelineBuilder.combine(
    pipelines=[standardization, logistic_regression],
    name="stz_lr",
    # two dependencies returned from input-output collection assignment
    dependencies=(logistic_regression.in_collections.X << standardization.out_collections.Z,),
)

display_dag(stz_lr)
```

Notice the simple assignment of the `stz_lr` pipeline's input and output collections.
This mechanism generalizes to any number of parameters that share the same entry names, which is
useful for operating on pipelines with varying number of entries.

### Parameter Types

Accessing `inputs` and `outputs` attributes of a pipeline returns a mapping of entry parameters;
accessing `in_collections` and `out_collections` returns a mapping of collections of parameters,
whose values are mappings of entry parameters.
These are the types from the nested mappings, accessible via dot notation for some examples we have
seen above:
|     `Pipeline`    |     `Inputs`       |    `InEntry`    |
|:-----------------:|:------------------:|:---------------:|
|    `stz_train`    |     `.inputs`      |    `.X`         |
|    `stz_eval`     |     `.inputs`      |    `.X`         |
|    `stz_eval`     |     `.inputs`      |    `.mean`      |
|    `stz_eval`     |     `.inputs`      |    `.scale`     |

|     `Pipeline`    |     `Outputs`      |    `OutEntry`   |
|:-----------------:|:------------------:|:---------------:|
|     `stz_train`   |     `.outputs`     |    `.Z`         |
|     `stz_train`   |     `.outputs`     |    `.mean`      |
|     `stz_train`   |     `.outputs`     |    `.scale`     |
|     `stz_eval`    |     `.outputs`     |    `.Z`    |

The pipeline exposing collections of entries:

|     `Pipeline`    |  `InCollections`   |  `InCollection` | `InEntry`  |
|:-----------------:|:------------------:|:---------------:|:----------:|
| `standardization` | `.in_collections`  |      `.X`       |  `.train`  |
| `standardization` | `.in_collections`  |      `.X`       |  `.eval`   |

|     `Pipeline`    |  `OutCollections`  | `OutCollection` | `OutEntry` |
|:-----------------:|:------------------:|:---------------:|:----------:|
| `standardization` | `.out_collections` |      `.Z`       |  `.train`  |
| `standardization` | `.out_collections` |      `.Z`       |  `.eval`   |

### Defaults for `UserInput` and `UserOutput`

Leaving `inputs` and `outputs` of `PipelineBuilder.combine` unspecified or set to `None` will
default their specificiation::

- All `inputs` or `outputs` from pipelines to combine will be merged, after subtracting any input
or output specified in the `dependencies` argument.
For example,

Leaving `inputs=None` is equivalent to

```python
inputs = {"X": standardization.in_collections.X, "Y": logistic_regression.in_collections.Y}
```

Entry `logistic_regression.inputs.X` is specified as a dependency, and is therefore not included
in the inputs of the combined pipeline.
Leaving `outputs=None` is equivalent to

```python
outputs = {
    "mean": standardization.outputs.mean,
    "scale": standardization.outputs.scale,
    "model": logistic_regression.outputs.model,
    "probs": logistic_regression.outputs.probs,
}
```

Only `standardization.outputs.Z` is specified in the dependencies list and excluded.

# TrainAndEval

In this tutorial we used `PipelineBuilders.combine` to build an ML pipeline - one that fits a model
on training data and evaluates that model on that training data and on a holdout data.

See [Tutorial: TrainAndEval](https://msft-amp.azurewebsites.net/atlas/notebooks/1ee191de-5f6d-4933-ba7c-16fa903205eb?path=elonp@microsoft.com/OneML/Tutorials/train_and_eval.ipynb) for OneML tools useful in this scenario
including simplifying and standardizing such pipelines, and using this standardization to
automatically persist fitted eval pipelines.
