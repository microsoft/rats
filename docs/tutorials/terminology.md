## Terminology

- **Pipeline:** A *pipeline* is formed by *nodes* and *dependencies*. We use the term as synonym of
*DAG*. *Pipelines* encode the execution order of nodes and dependencies between them.

- **DAG**: Directed acyclic graph. We use the term as synonym of *pipeline*.

- **Processor:** A class object with a *process* method implementing the 
`IProcess` [interface](advanced.md#defining-processors).
Executes instructions and operates on inputs and outputs.

- **Node**: Vertex, or compute point, of a *pipeline*.
Nodes hold references to *processor* classes, input & output parameters, constructor arguments and
compute requirements.
During orchestration, *processors* are instantiated and run from nodes encoded in the *pipeline*.

- **Dependency:** Directed edge between compute *nodes*.
The output of one *processor* feeds into the input of the next *processor*.
During orchestration, outputs are passed as inputs to the depending nodes.

- **Task:**

- **Estimator:**
