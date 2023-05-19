# Intermediate Tutorial

In the [beginners tutorial](beginners.md) we have seen how to construct `hello_world`, `diamond`
and `standardized_lr` pipelines.
In this tutorial we will dive deeper into some of the concepts we touched upon and discuss more
complicated use cases.

#### Table of Contents

- [Defining Tasks](#defining-tasks)
  - [Constructor Parameters](#constructor-parameters)
  - [Dynamic Annotations](#dynamic-annotations)
  - [Services](#services)
  - [IOManagers and Serializers](#iomanagers-and-serializers)
- [Combining Pipelines](#combining-pipelines)
  - [Parameter Entries](#parameter-entries)
  - [Parameter Collections](#parameter-collections)
  - [Parameter Types](#parameter-types)
  - [Defaults for `UserInput` and `UserOutput`](#defaults-for-userinput-and-useroutput)
- [Estimators](#estimators)

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
    [Services](advanced.md#services).
- `io_managers` (`Mapping[str, oneml.pipelines.session.IOManagerId]`): \[optional\] A mapping from
    output entries to `IOManagerId`, e.g., `{"model": IOManagerId("local")}`. If ommitted, default
    in-mermory `IOManager` is used.
- `serializers` (`Mapping[str, oneml.pipelines.DataTypeId]`): \[optional\] A mapping from output
    entries to `DataTypeId`, e.g., `{"model": DataTypeId("dill")}`. If ommitted, default
    mapping type is used (specified in the session). Not all `io_managers` require a `serializer`.
- `input_annotation` (`Mapping[str, type]`): \[optional\] dynamic inputs for variable keyword
    parameter, e.g., `**kwargs`; required if *processor* specifies
    [var keyword](https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind)
    parameters.
- `return_annotation` (`Mapping[str, type]`): \[optional\] dynamic outputs; overrides the
    *processors* return annotation. Useful when the number of outputs a processor returns varies
    between pipelines, and only known at build time, e.g., a data splitter for cross-validation.
- `compute_requirements` (`oneml.processors.PComputeReqs`): \[optional\] stores information about
    the resources the *processor* needs to run, e.g., CPUs, GPUs, memory, etc.

### Task execution

When the task is executed it performs the following:

- collect input values from upstream nodes.
- collect constructor parameters from `config`, `services` and inputs (see
    [Constructor Parameters](#constructor-parameters)).
- construct a processor object by calling the constructor of `processor_type` with the collected
    constructor parameters it collected.
- call the process method of the processor object, passing the relevant inputs.
- publish the outputs of the process method as the task outputs.

### Constructor Parameters

To construct a processor object, the task needs to provide a value for each parameter of the
constuctor of `processor_type`.

For each such parameter, the value will be provided in one of the following three ways:

- If the parameter appears in `config` its value is take from there.
- If the parameter appears in `services`, it is mapped to a service id.  The framework will look
    for the appropriate service provider in the services registry of the executing environment, and
    call it to provide a service object.  That service be the value for the parameter.
- If the parameter does not appear in `config` nor in `services`, it is assumed to be an input to
    the `task`.  Its value will be taken from those inputs.

The following example implements a data loader.

This example gets its constructor parameters from an in-memory immutable dictionary, i.e.,
`frozendict`.

Other mechanims for passing arguments are also supported, e.g., instantiating objects from
configuration.

```python
from typing import Any, Mapping, TypedDict

from oneml.processors import PipelineBuilder, frozendict

LoadDataOut = TypedDict("LoadDataOut", {"data": Any})


class LoadData:
    def __init__(self, storage: Mapping[str, float]):
        self._storage = storage

    def process(self, key: str) -> LoadDataOut:
        return LoadDataOut(data=self._storage["key"])


storage = frozendict({"X_train": 5, "X_eval": 1, "Y_train": 0, "Y_eval": 1})
load_data = PipelineBuilder.task(processor_type=LoadData, name="load_data", config=storage)
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
That is the reason why `oneml.processors.Task` accepts `input_annotation` and `return_annotation`
parameters.
For most *processors* these arguments will be unncessary, but if we provide them, they will
override the class's input or return signatures, respectively.
For example,

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

### Services

Services are objects that are provided to a processor as constructor parameters.
They are used to provide functionality that is provided by the executing environment, e.g.,
`SparkContext`, `WandbLogger`, etc.

Services are registered in the executing environment, and are mapped to service ids.

The following is an example of how to use a service within a task:

```python
from typing import Any, Mapping, TypedDict
from immunopipeline.jupyter_kernel.services import ImmunopipelineOnemlServices

class SparkExample:
    _spark_context: SparkContext

    def __init__(self, spark_context: SparkContext):
        self._spark_context = spark_context

    def process(self) -> None:
        ...

spark_example = PipelineBuilder.task(
    processor_type=SparkExample,
    name="spark_example",
    services={"spark_context": ImmunopipelineOnemlServices.SparkContext},
)
```


### IOManagers and Serializers

IOManagers are specific objects in charge of persisting data.
They are used to store the outputs of a task, and to retrieve the inputs of a task.

The framework provides a default in-memory IOManager, which is used if no other IOManager is
specified.
The default IOManager is not persistent, i.e., it will not store data between executions of the
framework.

Other IOManagers includo a `LocalFilesystemIOManager` and a `BlobIOManager`, which store
serializable data in the local filesystem or blob storage, respectively. 

We use custom IOManagers for `numpy`, `pandas` and `spark`, as these data structures use their
own persitenace mechanisms.

An example of how to persist an output using a local filesystem IOManager is the following:

```python
from typing import TypedDict
class Model:
    weights: tuple[float]
    bias: float

    def fit(self) -> None:
        ...

TrainModelOutput = TypedDict("TrainModelOutput", {"model": Model})

# Processor class
class TrainModel:
    _model: Model

    def __init__(self, model: Model):
        self._model = model

    def process(self) -> TrainModelOutput
        self._model.fit()
        return TrainModelOutput(model=self._model)

# Pipeline task
train_model = PipelineBuilder.task(
    TrainModel,
    io_managers={"model": IOManagerIds.LOCAL},
    serializers={"model": SerializerIds.DILL},
)
```

And example with a Spark DataFrame would be the following:

```python
from typing import TypedDict
from oneml.pipelines.session import IOManagerId

FetOutputs = TypedDict("CalcTcrFetOutputs", { "tcr_score_df": DataFrame })

class CalculateTcrFet:
    def __init__(self, label_column="label"):
        self._label_column = label_column
        self._allowed_labels = (0, 1)

    def process(self, num_positives: int, num_negatives: int , sequences_df: DataFrame) -> CalcTcrFetOutputs:
        ...
        return FetOutputs(tcr_score_df = tcr_pval.localCheckpoint(eager=True))

count_samples_per_label = PipelineBuilder.task(
    CalcTcrFet,
    config={"label_column": label_column},
    iomanagers = {"tcr_score_df": IOManagerId("spark-local")}
)
```

Finally, the following constitutes an advanced example of how to register custom IOManagers and
Serializers into the framework.
These operations happen in the DI container before any session is created.

The `IOManagerRegistry` and the `SerializerClient` are used to register custom IOManagers and
serialiers, respectively.
The `MappedPipelineDataClient` is used to map data types to serializers automatically.

```python
from typing import Any
from oneml_test.processors.mock_data import Array, Model, ModelSerializer
from oneml.pipelines.data._serialization import DillSerializer, SerializationClient, SerializerIds
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._local_data_client import IOManagerIds, LocalDataClient
from oneml.pipelines.session import DataTypeId, IOManagerId, IOManagerRegistry

class IOManagerIds:
    LOCAL = IOManagerId("local")

class DataTypeIds:
    ARRAY = DataTypeId[Array]("array")
    MODEL = DataTypeId[Model]("model")

class SerializerIds:
    DILL = DataTypeId[Any]("dill")

serialization_client = SerializationClient()
serialization_client.register(type_id=DataTypeIds.MODEL, serializer=ModelSerializer())
serialization_client.register(type_id=SerializerIds.DILL, serializer=DillSerializer())

type_mapping = MappedPipelineDataClient()

local_pipeline_data_client = LocalDataClient(
    serializer=serialization_client,
    type_mapping=type_mapping,
    session_context=pipeline_session_context,
)

registry = IOManagerRegistry()
registry.register(IOManagerIds.LOCAL, local_pipeline_data_client)
```

## Combining Pipelines

We will further explain how to combine pipelines, handle name conflicts, and expose inputs and
outputs.

### PipelineBuilder.combine

The exact parameter signature of `PipelineBuilder.combine` is the following:

- `*pipelines` (`Pipeline`): a sequence of `Pipeline`s to combine; must have different names.
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

#### Requirements

- All *inputs* to the pipeline must be specified if `inputs` is not `None`.

- Exposing `outputs` is optional.
- `UserInput` or `UserOutput` can have at most single dot in the *mapping* keys.
An error will be raised otherwise.
Consider the following `standardization` example:

```python
from typing import TypedDict

from oneml.processors import PipelineBuilder

StandardizeTrainOut = TypedDict("StandardizeTrainOut", {"mean": float, "scale": float, "Z": float})
StandardizeEvalOut = TypedDict("StandardizeEvalOut", {"Z": float})


class StandardizeTrain:
    def process(X: float) -> StandardizeTrainOut:
        ...


class StandardizeEval:
    def __init__(self, mean: float, scale: float) -> None:
        ...

    def process(X: float) -> StandardizeEvalOut:
        ...


stz_train = PipelineBuilder.task(StandardizeTrain)
stz_eval = PipelineBuilder.task(StandardizeEval)

standardization = PipelineBuilder.combine(
    stz_train,
    stz_eval,
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
In [begginer's tutorial](beginners.md) we saw another example:

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
LogisticRegressionTrainOut = TypedDict(
    "LogisticRegressionTrainOut", {"model": tuple[float], "Z": float}
)
LogisticRegressionEvalOut = TypedDict("LogisticRegressionEvalOut", {"Z": float, "probs": float})


class LogisticRegressionTrain:
    def process(X: float, Y: float) -> LogisticRegressionTrainOut:
        ...


class LogisticRegressionEval:
    def __init__(self, model: tuple[float, ...]) -> None:
        ...

    def process(X: float, Y: float) -> LogisticRegressionEvalOut:
        ...


lr_train = PipelineBuilder.task(LogisticRegressionTrain, name="lr_train")
lr_eval = PipelineBuilder.task(LogisticRegressionEval, name="lr_eval")

logistic_regression = PipelineBuilder.combine(
    lr_train,
    lr_eval,
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
    standardization,
    logistic_regression,
    name="stz_lr",
    # two dependencies returned from input-output collection assignment
    dependencies=(logistic_regression.in_collections.X << standardization.out_collections.Z,),
)
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

# Estimators

[Combining pipelines](#combining-pipelines) for creating train and eval tasks so far:

1. Instantiate tasks, e.g., `stz_train`, `stz_eval`, `lr_train`, `lr_eval`.
2. Combine tasks, e.g., `standardization`, `logistic_regression`.
3. Specify dependencies, e.g., `stz_eval.inputs.mean << stz_train.outputs.mean`,
`lr_eval.inputs.model << lr_train.outputs.model`.
4. Specify inputs and outputs, e.g.,
`inputs={"X.train": stz_train.inputs.X, "X.eval": stz_eval.inputs.X}`.
5. Combine pipelines passing dependencies, inputs and outputs.
This pattern can be simplified with estimators:
1. Instantiate tasks, e.g., `stz_train`, `stz_eval`, `lr_train`, `lr_eval`.
2. Instantiate estimators, e.g., `standardization`, `logistic_regression`.
4. Combine estimators, e.g., `stz_lr` below.

```python
from oneml.processors.ml import Estimator

# Instantiate tasks
stz_train = PipelineBuilder.task(StandardizeTrain)
stz_eval = PipelineBuilder.task(StandardizeEval)
lr_train = PipelineBuilder.task(LogisticRegressionTrain)
lr_eval = PipelineBuilder.task(LogisticRegressionEval)

# Instantiate estimators
standardization = Estimator(
    name="standardization",
    train_pl=stz_train,
    eval_pl=stz_eval,
    dependencies=(
        stz_eval.inputs.mean << stz_train.outputs.mean,
        stz_eval.inputs.scale << stz_train.outputs.scale,
    ),
)
logistic_regression = Estimator(
    name="logistic_regression",
    train_pl=lr_train,
    eval_pl=lr_eval,
    dependencies=(lr_eval.inputs.model << lr_train.outputs.model,),
)

# Combine estimators
stz_lr = PipelineBuilder.combine(
    standardization,
    logistic_regression,
    name="stz_lr",
    dependencies=(logistic_regression.in_collections.X << standardization.out_collections.Z,),
)
```

The main advantage for using estimators is that collections are built so that they are compatible
to operate together.
If the previous *processors* had more than one evaluation task, the underlying dependency
assignments do not change if they rely on collection assignments.
> :notebook: **Note:**
Combinging pipelines using `Estimator` exposes all outputs from both pipelines.
That is why `standardization` exposes `mean` and `scale`, and why `logistic_regression` exposes
`model`, even though they are specified as dependencies.
This is not the default behavior of `PipelineBuilder.combine`, which does not expose outputs that
have been specified as dependencies.
