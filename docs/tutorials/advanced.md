# Advanced Tutorial

In this tutorial we will dive deeper into concepts, and will allow you to build your own ML
meta-pipelienes or to use OneML with other configuration tools via a plugin system.

The first use case is to build *processors* with constructors.

## Defining *Processors*

The definition of a *processor* is simple.
It's any object that implements the `IProcess` interface:

```python
from typing import Any, Callable, Mapping, Protocol

class IProcess(Protocol):
    process: Callable[..., Mapping[str, Any] | None]
```

Here, `IProcess` extends `Protocol`, which is a Python builtin class to define interfaces.
In practice it means that *processors* do not need to extend `IProcess`, they just need to
implement the `IProcess` interface.
This is useful because you are guaranteed that the `IProcess` interface does not modify your
*processor* in ways you didn't anticipate.

Below is a simple example:

```python
from oneml.processors import IProcess

class ExampleProcessor(IProcess):
    def __init__(self, ...) -> None:
        ...

    def process(self) -> None:
        ...
```

The `IProcess` interface simply requires that you implement a `process` method, and returns a
`Mapping[str, Any]` or `None`.
The `process` method can take any number of arguments of Python supported
[kinds](https://docs.python.org/3/library/inspect.html#inspect.Parameter.kind).

You may extend your *processors* from `IProcess` or not, but the framework will validate that you
satisfy the required interface.


## Defining `params_getter`s:

The argument `params_getter` from `oneml.processors.PipelineClient.task` expects an immutable,
serializable *mapping*.

We have seen in the [intermediate tutorial](intermediate.md#defining-tasks) an example of such
data structure, i.e., `frozendict`s.
However, this is not the only datastructure you can pass in, and any object satisfying the
`IGetParams` interface will work:

```python
from typing import Any, Hashable, Protocol
from oneml.processors import MappingProtocol

class IGetParams(MappingProtocol[str, Any], Hashable, Protocol):
    """Hashable mapping (protocol) for retrieving parameters to construct & execute an IProcess."""
```

This interface (*Protocol*) requires that the implementation is a *Mapping* and *Hashable*.

`Mapping` is an abstract collection that requires that an object implements `__get_item__` method
(among others), and exposes `keys`, `values` and `items`.
The full set of requirements for an object to be a `Mapping` are described in the official Python
[docs](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes).
Examples of `Mapping`s include `dict` or our implementation `frozendict` (which is an immutable
dictionary):

| Collection   | Extends                                               |
|--------------|-------------------------------------------------------|
| `dict`       | `collections.abc.MutableMapping`                      |
| `frozendict` | `collections.abc.Mapping`, `collections.abc.Hashable` |
|              |                                                       |

*Hashable* requires that the object implements a `__hash__` method.
An object that implements it is considered immutable, and its attributes should not be changed once
instantiated (at the risk of inconsistent behavior).

Serilizability is important if you require that the processor runs in a distributed environment, so
that we can serialize and de-serialize the object on different machines.
Using `frozendict` is a reliable way to accomplish that, in contrast to standard `dict`s, which are
mutable.
We also support other alternatives via plugins that satisfy the `Mapping` protocol and are
serializable too, such as *Hydra* configuration tool.

Immutability (*hashable*) is akin to serializability, although not exactly the same.
There is no abstract collection to extend *serializability*, so we extend `Hashable` only.


########


#### `PipelineInput` & `PipelineOutput`:

You can subtract single or collection of parameters:
```
new_incollection.inputs - new_incollection.X.train
new_incollection.inputs - new_incollection.inputs.X
```

You can merge pipeline inputs & outputs:
```
standardization.inputs | (logistic_regression.inputs - logistic_regression.inputs.X).
```
With this operation collissions are not permitted and will error if they exist:
```
standardization.inputs | logistic_regression.inputs  # error
```
