## Pipeline Data

The `PipelineData` class provides access to any `PipelinePort` that has been published so far
in the execution of the pipeline. The default implementation is a simple `dict` of published
data. However, this can be extended to provide more sophisticated data access, such as a
database or a distributed file system.

With single-node pipelines, the `PipelineData` class is used to provide access to the data and to
implement plugins that persist data to disk, like the `LocalJsonIoPlugin`, described below.

## IO Plugins

The `RatsIoPlugin` protocol can be implemented to create IO plugins that get notified of
completed pipeline nodes.

## Local JSON IO Plugin

The `LocalJsonIoPlugin` plugin gives people the ability to specify a set of pipeline ports to
persist as JSON files on the local filesystem. The ports are persisted after the successful
execution of the associated pipeline node. The functionality is implemented by the
`LocalJsonWriter` and pipeline authors can register ports to be persisted using the
`LocalJsonStorage` service.

```python
from rats.io2 import LocalJsonIoSettings
from rats.pipelines.building import PipelineBuilderClient
from rats.services import IExecutable
from rats.pipelines.dag import PipelinePort


class ExamplePipeline(IExecutable):
    _builder: PipelineBuilderClient
    _json_storage: LocalJsonIoSettings
    ...

    def execute(self) -> None:
        ...
        self._json_storage.register_port(self._builder.node("foo"), PipelinePort("bar"))
```

## Local IO Settings

The `LocalIoSettings` class provides a way to specify the location of the local IO directory
where IO plugins should persist data. It's used by the `LocalJsonIoPlugin` and can be configured
during the definition of a pipeline.

```python
from pathlib import Path

from rats.io2 import LocalIoSettings
from rats.pipelines.building import PipelineBuilderClient
from rats.services import IExecutable


class ExamplePipeline(IExecutable):
    _local_io_settings: LocalIoSettings
    ...

    def execute(self) -> None:
        ...
        self._local_io_settings.set_data_path(Path("/mnt/big-data"))
```
