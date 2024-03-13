# Contributor's Guide

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
from rats.processors import IProcess

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
