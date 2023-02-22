# oneml-habitats

## Missing Features

### Remote Node Execution

#### Session Client Registry

In order to support a pipeline node running remotely, we need to be able to create the session
object with node names and executables in the remote process.

```
ONEML_HABITATS_PIPELINE=hello-world-demo
ONEML_PIPELINE_SESSION_ID=1234abcd
immunocli-next oneml run-pipeline-node "//a"
```

In habitats, we're implementing this with a registry class that maps a string name
(hello-world-demo), to a callable that returns a session client. We can use this on the driver to
implement `immunocli-next oneml run-pipeline hello-world-demo`, and on the remote node, to
implement the command that calls `session.run_node("//a")`.

## Organization

- `PipelineServiceClient` is a top-level client that can be used to create sessions
- `PipelineServiceClient` should use factory classes to initialize builders for new sessions
- `PipelineServiceClient` generates a new session id when creating a new session
- `PipelineServiceClient` can load a session when given a session id
- `PipelineComponents` instance belongs to a session and shares instances within the session
- `PipelineSettings` instance belongs to the process so changes affect all sessions
- `PipelineSessionSettings` instance belongs to a session and overrides `PipelineSettings` entries
- `PipelineNodeSettings` instance belongs to a node and overrides `PipelineSessionSettings` entries
- `PipelineBuilder` contains methods to define the DAG
- `PipelineExecutables` maps nodes to provider callback for executable instances
- switch to using the above settings classes for remote node execution
- switch to using the above settings classes for data client settings
- `PipelineSession` is tied to a single execution of a pipeline and has a unique session id (uuid)
- `PipelineSessionContext` is tied to the process and retrieves the currently executing session

## Questions

- when running multi-image pipelines, how do verify that the session component is available in the target image when building?
  - maybe we have metadata libraries that you install on the driver that gives us the info needed to know available images and their components
