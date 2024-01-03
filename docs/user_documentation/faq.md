

# FAQ

### What is OneML?

OneML is a framework to design and run pipelines for ML Research.
Users organize their code writing classes which include ML functions and specify inputs and
outputs.
Users design pipelines linking these functions together and can run them.


### Why is OneML different from other ML pipelines tools?

There are many pipelines tools offered for ML, but these are mainly focused on the orchestration of
operations, including data preparation, training, service of trained products, product quality
evaluations, among other features.

These tools require users to organize their code in scripts or commands, to serialize and
de-serialize their inputs and outputs, to write the edges across operations and finally to run or
publish archetype pipelines whose parameters can later be specified.

We find that without appropriate design conventions, input / output connecting mechanisms,
convenient pipeline design language, composability and compatible functionality, these
tools require large time and rewritting overhead that make them difficult to use in research
environments.
Existing tools do not facilitate this functionality and it is not easy for multiple authors to
write code that can be easily interconnected, or to specify and modify pipelines easily.

OneML aims to facilitate building, composing, sharing and running ML pipelines easily and quickly.
OneML leverages existing orchestrating tools to create and run pipelines, while providing the tools
to organize functionality around classes rather than scripts or commands, to provide mechanisms
to interconnect inputs and outputs while abstracting serialization, and to facilate editing,
composition and sharing of pipelines.


### Why is OneML aimed for research?

Research is a fast paced environment where pipeline design should be flexible, abstract complex
functionality, and where ML concepts are built in to facilitate validity and analysis of results.

OneML provides a framework to connect code organized in classes, abstract the complexities from
running distributedly in multiple nodes, and facilitates organizing data around train and
evaluation splits, supporting cross-validation, hyperaparameter optimizatino, and other pipeline
wrappers that are commonly used.
