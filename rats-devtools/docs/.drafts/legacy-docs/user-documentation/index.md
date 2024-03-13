## Terminology

- **Pipeline:** A *pipeline* is formed by *nodes* and *dependencies*. We use the term as synonym of
*DAG*. *Pipelines* encode the execution order of nodes and dependencies between them.

- **DAG**: Directed acyclic graph. We use the term as synonym of *pipeline*.

- **Processor:** A class object with a *process* method. Implements on operation taking inputs and
producing outputs. The signatures of the processor's constructor and process method define the
inputs and outputs of the pipeline's *node*.

- **Node**: Vertex, or compute point, of a *pipeline*.
Nodes hold references to *processor* classes, input & output parameters, constructor arguments and
compute requirements. During orchestration, *processors* are instantiated and run from nodes
encoded in the *pipeline*.

- **Port**: Input or output of a *node*. *Output ports* are connected into *input ports* forming
a dependency, where the output of a *processor* is given as input to the receiving *processor*.

- **Dependency:** Directed edge from a *node's* output port to another *node's* input port.
The output of one *processor* feeds into the input of the next *processor*.
During orchestration, outputs are passed as inputs to the depending nodes.

- **Task:** A single node pipeline, created by wrapping over a *processor's* class.

- **TrainAndEval:** A classical ML pipeline, taking training data and eval data, learning a model using the training data, and using it to provide predictions on both training and eval data.  Rats provides tools to help build and manipulate TrainAndEval pipelines, including automatically persisting a fitted eval pipeline that can take other eval data and provide predictions.
