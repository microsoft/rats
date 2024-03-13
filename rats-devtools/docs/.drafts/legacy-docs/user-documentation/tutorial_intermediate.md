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
- [Combining Pipelines](#combining-pipelines)
  - [Parameter Ports: `InPort` and `OutPort`](#parameter-ports-inport-and-outport)
  - [Parameter Collections: `Inputs` and `Outputs`](#parameter-collections-inputs-and-outputs)
  - [Parameter Types](#parameter-types)
  - [Defaults for `UserInput` and `UserOutput`](#defaults-for-userinput-and-useroutput)
- [TrainAndEval](#trainandeval)
- [Pipeline Annotations](#pipeline-annotations)
- [Pipeline Providers](#pipeline-providers)

## Defining Tasks

A *task* is a pipeline of a single node.
Creating a task requires specifying the pararameters needed for the *processor* to be
initialized, i.e., configuration, dynamic input and output annotations, and compute
requirements.
A *task* has the following construct parameters:

- `processor_type` (`type[rats.processors.IProcess]`): a reference to the processor's class.
- `name` (`str`): \[optional\] name of the task. If missing, `processor_type.__name__` is used.
- `config` (`Mapping[str, Any]`): \[optional\] A mapping from (a subset of) the the processor's
    constructor parameters to values. The values need to be serializable if running in a
    distributed environment.
- `services` (`Mapping[str, rats.pipelines.session.ServiceId[Any]]`): \[optional\] A mapping from
    (a subset of) the the processor's constructor parameters to service ids.
    See [Services](tutorial_advanced.md#services).
- `input_annotation` (`Mapping[str, type]`): \[optional\] dynamic inputs for variable keyword
    parameter, e.g., `**kwargs`; required if *processor* specifies
    [var keyword](https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind)
    parameters.
- `return_annotation` (`Mapping[str, type]`): \[optional\] dynamic outputs; overrides the
    *processors* return annotation. Useful when the number of outputs a processor returns varies
    between pipelines, and only known at build time, e.g., a data splitter for cross-validation.
- `compute_requirements` (`rats.processors.PComputeReqs`): \[optional\] \[for future use\] stores
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
from rats.processors.ux import PipelineBuilder, display_dag
from rats.processors.dag import display_dag

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
    config=dict(output_folder=Path(".tmp"), file_name="a.csv"),
)

display_dag(save_pandas_1)
```

Or, we can ommit some of them and they will become an inputs the the task:

```python
save_pandas_2 = PipelineBuilder.task(processor_type=SavePandas, config=dict(file_name="a.csv"))

display_dag(save_pandas_2)
```

Finally, we can ask the framework to provide a service object as the value of a contructor
argument, like this:

```python
from immunoshare.rats.io import ImmunoshareRatsIoServices

save_pandas_3 = PipelineBuilder.task(
    processor_type=SavePandas,
    config=dict(file_name="a.csv"),
    services=dict(output_folder=ImmunoshareRatsIoServices.TMP_PATH),
)

display_dag(save_pandas_3)
```

Let's take a minute to execute these three pipelines.

We'll need a pipeline runner factory:

```python
from pathlib import Path
from rats.processors import RatsProcessorsServices

pipeline_runner_factory = rats_service_provider.get_service(
    RatsProcessorsServices.PIPELINE_RUNNER_FACTORY)
```

And we'll need to provide a dataframe as input:

```python
df = pd.DataFrame(dict(A=[10, 20, 30], B=["a", "b", "c"]))
```

Executing the first version, providing `df`, and then inspecting the `file_path` output:
```python
runner = pipeline_runner_factory(save_pandas_1)
outputs = runner(dict(df=df))
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
outputs = runner(dict(df=df, output_folder=Path("my_output_folder/")))
print(outputs.file_path)
with outputs.file_path.open() as r:
    print(r.read())
```

Executing the third version.  Here we trust `RatsHabitatsServices.TMP_PATH` to define the output
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
`rats.processors.Task` accepts `input_annotation` and `return_annotation` parameters.

For most *processors* these arguments will be unncessary, but if we provide them, they will
override the class's input or output signatures, respectively.

For example:
```python
from rats.processors import PipelineBuilder

io_annotation = {"foo": str, "boo": bool, "bee": int}
t = PipelineBuilder.task(Identity, input_annotation=io_annotation, return_annotation=io_annotation)
```

> :notebook: **Note**:
Recall that the return annotation of a processor may be a `NamedTuple`, `TypedDict` or `None`.
Passing `return_annotation=None` (default) will not override the *processor's* return signature.
Only if the return signature of a processor is `None` AND if `return_annotation=None`,
will the framework assume that the *processor* return type is actually `None`.
Same applies to `input_annotation=None`.

## Combining Pipelines

We will further explain how to combine pipelines, handle name conflicts, and expose inputs and
outputs.

### PipelineBuilder.combine

The exact parameter signature of `PipelineBuilder.combine` is the following:

- `pipelines` (`Sequence[Pipeline]`): the list of `Pipeline`s to combine; must have different names.
- `name` (`str`): name of the returned, combined pipeline.
- `dependencies` (`Iterable[Sequence[rats.ux.Dependency]]`): dependencies between the pipelines to
    combine, e.g., `(stz_eval.inputs.mean << stz_train.outputs.mean,)`.
- `inputs` (`rats.ux.UserInput | None`): mapping names of inputs of the pipelines to combine.
- `outputs` (`rats.ux.UserOutput | None`): mapping names of outputs of the pipelines to combine.

Arguments `inputs` and `outputs` are optional and help configure the exposed input and output
variables of the combined pipeline.

The exact definitions are the following:

- `UserInput = Mapping[str, rats.ux.InPort | rats.ux.Inputs]`
- `UserOutput = Mapping[str, rats.ux.OutPort | rats.ux.Outputs]`

Default behavior for `inputs` and `outputs` set to None is explained in the
[section](#defaults-for-userinput-and-useroutput) below.

> :notebook: **Note:**
Dependencies are not expected to be created manually, but through the `<<` operator syntax.

Consider the following `standardization` example:

```python
from typing import NamedTuple
from rats.processors import PipelineBuilder

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

### Parameter ports: `InPort` and `OutPort`

We have specified dependencies between input and output ports for `stz_train` and `stz_eval`
using the `<<` operator:

```python
stz_eval.inputs.mean << stz_train.outputs.mean
stz_eval.inputs.scale << stz_train.outputs.scale
```

We access single input and output ports of the pipelines via the `inputs` and `outputs` attributes.
This happens with `stz_eval.inputs.mean` and `stz_train.outputs.mean`.
In [begginer's tutorial](tutorial_beginners.md) we saw another example:

```python
stz_lr_dependencies = (
    logistic_regression.inputs.X_train << standardization.outputs.Z_train,
    logistic_regression.inputs.X_eval << standardization.outputs.Z_eval,
)
```

> :notebook: **Note**:
In these examples the *processors*' inputs and outputs had unique names.
If the variable parameters don't have unique names, we can expose them as collections of
parameters, as explained in the next section.

### Parameter collections: `Inputs` and `Outputs`

Pipelines `stz_train` and `stz_eval` both expose `X` and `Z` variable names so we needed to
specify how `X` and `Z` are combined together.
In the `PipelineBuilder.combine` example from above we have written:

```python
inputs={"X.train": stz_train.inputs.X, "X.eval": stz_eval.inputs.X},
outputs={"Z.train": stz_train.outputs.Z, "Z.eval": stz_eval.outputs.Z}
```

The combined pipeline will expose variables as collections of parameters:

```python
standardization.inputs.X  # Inputs object
standardization.outputs.Z  # Outputs object
```

Both `standardization.inputs.X` and `standardization.outputs.Z` gather two inputs
and two outputs entries, respectively.
The individual entries are accessible via:

```python
standardization.inputs.X.train  # InPort objects
standardization.inputs.X.eval
standardization.outputs.Z.train  # OutPort objects
standardization.outputs.Z.eval
```

The usefulness of collections is that we can group parameters together and create dependencies.
Here another example with `logistic_regression`:

```python
from typing import NamedTuple
from rats.processors import PipelineBuilder

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
logistic_regression.outputs.probs  # OutPort object

logistic_regression.inputs.X  # Inputs objects
logistic_regression.inputs.Y
logistic_regression.outputs.Z  # Outputs object

logistic_regression.inputs.X.train  # InPort objects
logistic_regression.inputs.X.eval
logistic_regression.inputs.Y.train
logistic_regression.inputs.Y.eval
logistic_regression.outputs.Z.train  # OutPort objects
logistic_regression.outputs.Z.eval
```

Finally, we can combine `standardization` and `logistic_regression` together:

```python
stz_lr = PipelineBuilder.combine(
    pipelines=[standardization, logistic_regression],
    name="stz_lr",
    # two dependencies returned from input-output collection assignment
    dependencies=(logistic_regression.inputs.X << standardization.outputs.Z,),
)

display_dag(stz_lr)
```

Notice the simple assignment of the `stz_lr` pipeline's input and output collections.
This mechanism generalizes to any number of parameters that share the same entry names, which is
useful for operating on pipelines with varying number of entries.

### Parameter Types

Accessing `inputs` and `outputs` attributes of a pipeline returns a mapping of port parameters
(`InPort`, `OutPort`) or collection of port parameters (`Inputs`, `Outputs`)

These are the types from the nested mappings, accessible via dot notation for some examples we have
seen above:
|     `Pipeline`    |     `Inputs`       |     `InPort`    |
|:-----------------:|:------------------:|:---------------:|
|    `stz_train`    |     `.inputs`      |    `.X`         |
|    `stz_eval`     |     `.inputs`      |    `.X`         |
|    `stz_eval`     |     `.inputs`      |    `.mean`      |
|    `stz_eval`     |     `.inputs`      |    `.scale`     |

|     `Pipeline`    |     `Outputs`      |    `OutPort`    |
|:-----------------:|:------------------:|:---------------:|
|     `stz_train`   |     `.outputs`     |    `.Z`         |
|     `stz_train`   |     `.outputs`     |    `.mean`      |
|     `stz_train`   |     `.outputs`     |    `.scale`     |
|     `stz_eval`    |     `.outputs`     |    `.Z`    |

The pipeline exposing collections of entries:

|     `Pipeline`    |     `Inputs`       |    `Inputs`     |  `InPort`  |
|:-----------------:|:------------------:|:---------------:|:----------:|
| `standardization` |     `.inputs`      |      `.X`       |  `.train`  |
| `standardization` |     `.inputs`      |      `.X`       |  `.eval`   |

|     `Pipeline`    |     `Outputs`      |    `Outputs`    |  `OutPort` |
|:-----------------:|:------------------:|:---------------:|:----------:|
| `standardization` |     `.outputs`     |      `.Z`       |  `.train`  |
| `standardization` |     `.outputs`     |      `.Z`       |  `.eval`   |

As you can see, parameter ports can be combined together into nested collections.
This is achieved via specifying inputs and outputs when combining pipelines together or via
[parameter renames](tutorial_advanced.md) using dot notation as in the example above.


### Defaults for `UserInput` and `UserOutput`

Leaving `inputs` and `outputs` of `PipelineBuilder.combine` unspecified or set to `None` will
default their specificiation:

- All `inputs` or `outputs` from pipelines to combine will be merged, after subtracting any input
or output specified in the `dependencies` argument.

For example, leaving `inputs=None` when combining `standardization` and `logistic_regression`
is equivalent to

```python
inputs = {"X": standardization.inputs.X, "Y": logistic_regression.inputs.Y}
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
    "Z": logistic_regression.outputs.Z,
}
```

Only `standardization.outputs.Z` is specified in the dependencies list and excluded.
Furthremore, pecifying `Z` output could also have been done more verbosely:
```python
{
    ...,
    "Z.train": logistic_regression.outputs.Z.train,
    "Z.eval": logistic_regression.outputs.Z.eval
}
```

## TrainAndEval

In this tutorial we used `PipelineBuilders.combine` to build an ML pipeline - one that fits a model
on training data and evaluates that model on that training data and on a holdout data.

See [Tutorial: TrainAndEval](https://msft-amp.azurewebsites.net/atlas/notebooks/1ee191de-5f6d-4933-ba7c-16fa903205eb?path=elonp@microsoft.com/Oneml/Tutorials/train_and_eval.ipynb) for Rats tools useful in this scenario
including simplifying and standardizing such pipelines, and using this standardization to
automatically persist fitted eval pipelines.


## Pipeline Annotations

Given a pipeline, it may be ambiguous knowing if a certain attribute is an input/output port,
or a collection.
When building a pipeline, you can declare its inputs and outputs, so that users of that pipeline
will get automatic IDE completion, as well as explicit type declaration of the attribute
in question.

This feature is completely optional, not enforced, and only helps in production environments when
the author of a pipeline wants to declare the inputs and outputs of the pipeline for readability
and autocompletion for other users consuming it.

Annotated pipelines allow building a *catalog* of pipelines, and get a clear understanding of what
inputs and outputs each pipeline exposes, and how they can be combined together.

For example:
```python
from rats.processors.ux import Inputs, Outputs, InPort, OutPort

class XIn(Inputs):
    X: InPort[float]

class XMeanScaleIn(Inputs):
    X: InPort[float]
    mean: InPort[float]
    scale: InPort[float]

class ZOut(Outputs):
    Z: OutPort[float]

class ZMeanScaleOut(Outputs):
    Z: OutPort[float]
    mean: OutPort[float]
    scale: OutPort[float]

stz_train = PipelineBuilder[XIn, ZMeanScaleOut].task(StandardizeTrain)
stz_eval = PipelineBuilder[XMeanScaleIn, ZOut].task(StandardizeEval)

# statically evaluated and completed with IDE
stz_eval.inputs.mean << stz_train.outputs.mean  # identified as InPort << OutPort on hover
stz_eval.inputs.scale << stz_train.outputs.scale   # identified as InPort << OutPort on hover
```

When combining variables together, nested declaration is possible:
```python
class TrainEvalIn(Inputs):
    train: InPort[float]
    eval: InPort[float]

class TrainEvalZOut(Outputs):
    train: OutPort[float]
    eval: OutPort[float]

class StzIn(Inputs):
    X: TrainEvalIn

class StzOut(Outputs):
    Z: TrainEvalZOut
    mean: OutPort[float]
    scale: OutPort[float]

stz = PipelineBuilder[StzIn, StzOut].combine(
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
    }
)
# statically evaluated and completed with IDE
stz.inputs.X  # identified as Inputs
stz.inputs.X.train # identified as InPort
stz.inputs.X.eval  # identified as InPort
stz.outputs.Z  # identified as Outputs
stz.outputs.Z.train  # identified as OutPort
stz.outputs.Z.eval  # identified as OutPort
stz.outputs.mean  # identified as OutPort
stz.outputs.scale  # identified as OutPort
```

Under the hoods, `Pipeline` is a [generic](https://mypy.readthedocs.io/en/stable/generics.html)
of two typed variables, i.e., the pipeline inputs and outputs:
```python
from typing import Generic, TypeVar

TInputs = TypeVar("TInputs", bound=Inputs, covariant=True)
TOutputs = TypeVar("TOutputs", bound=Outputs, covariant=True)

class Pipeline(Generic[TInputs, TOutputs]):
    ...
```
This mechanism allow Pipelines to be annotated as we have seen in the builders above:
```python
stz = PipelineBuilder[StzIn, StzOut].combine(...)
stz  # Pipeline[StzIn, StzOut]
```


## Pipeline Providers

Sharing pipelines between users is done via *pipeline providers*.
These providers may encapsulate specialized functionality that a pipeline author shares with
other users and make it reusable.

> :bulb: **Important**:
Modularity and reusability are two core design principles that we promote when building pipelines.

The following mechanism can be used to make a pipeline provider available.
Note that this mechanism leverages the RatsApp concepts explained in `rats-pipelines`. TODO: need link.

First declare your pipeline provider service.
Second, add your service to the `RatsProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS` group.

For example in `example/_app_plugin.py`:

```python
from rats.processors.registry import (
    IProvidePipeline,
    IProvidePipelineCollection,
    RatsProcessorsRegistryServiceGroups,
    ServiceMapping,
)
from rats.services import (
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_group,
    service_provider,
)

from ._pipeline import DiamondExecutable, DiamondPipeline, DiamondPipelineProvider

@scoped_service_ids
class _PrivateServices:
    DIAMOND_PIPELINE_PROVIDER = ServiceId[IProvidePipeline[DiamondPipeline]]("diamond-provider")

class DiamondExampleDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.DIAMOND_PIPELINE_PROVIDER)
    def diamond_pipeline_provider(self) -> DiamondPipelineProvider:
        return DiamondPipelineProvider()

    @service_group(RatsProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS)
    def diamond_pipeline_providers_group(self) -> IProvidePipelineCollection:
        diamond = _PrivateServices.DIAMOND_PIPELINE_PROVIDER
        return ServiceMapping(services_provider=self._app, service_ids_map={"diamond": diamond})

class DiamondExampleServices:
    DIAMOND_PIPELINE_PROVIDER = _PrivateServices.DIAMOND_PIPELINE_PROVIDER
```

Here, we are adding a new service provider with `ServiceId` identified via
`DiamondExampleServices.DIAMOND_PIPELINE_SERVICE`.
Furthermore, this service provider is then added to the
`RatsProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS` service group.

Every users will be now able to call the pipeline provider by referring to the individual
service id, or even call all pipeline providers after making it available to the service group
(which is used in YAML pipelines for example).

The `rats.processors.registry.IProvidePipeline` interface to create a pipeline provider is
defined as follows
```python
from typing import Protocol, TypeVar
from rats.processors.ux import UPipeline

Tco_Pipeline = TypeVar("Tco_Pipeline", bound=UPipeline, covariant=True)

class IProvidePipeline(Protocol[Tco_Pipeline]):
    def __call__(self) -> Tco_Pipeline:
        ...
```

Note that `IProvidePipeline` is a
[generic protocol](https://mypy.readthedocs.io/en/stable/generics.html#generic-protocols)
optionally accepting a `Pipeline` typed variable (such as an annotated pipeline).
