"""
Thoughts on the definition of an app, a pipeline, and a dag.

- an app is just a single executable
- the pipeline app is an instance of an app that tries to run a pipeline
- an execution of a pipeline app is done in an app session
- a dag is an internal detail to pipeline apps
- we have many instances of apps
- some of them expose plugins
  - plugins just have the ability to register services
- ImmunocliCliApp
- RatsApp
  - this is the only pipeline app
"""
