# %% [markdown]
# ## Tutorial: self-contained pipeline classes
# %%
import rats.processors as rp
from rats import apps

app = rp.NotebookApp()

# %% [markdown]

# # Single node pipeline
# A pipeline node holds a reference to a processor, i.e. the function that will be executed when
# the node is run.
# The processor function is expected to take annotated arguments and return a NamedTuple.  The
# annotations will become the pipeline's inputs, and the entries of the NamedTuple will become the
# pipeline's outputs.
# To create a single node pipeline, create a class that inherits from `PipelineContainer` and
# annotate a method with the `task` decorator.

# %%
from typing import NamedTuple


class _SumOutput(NamedTuple):
    result: float
    log_message: str


class SimplePipelineContainer(rp.PipelineContainer):
    @rp.task
    def sum(self, a: float, b: float) -> _SumOutput:
        result = a + b
        log_message = f"{a} + {b} = {result}"
        return _SumOutput(result=result, log_message=log_message)


spc = SimplePipelineContainer()


# %% [markdown]

# The `task` decorator converts the method into a method that takes nothing and returns a function:

# %%
import inspect

print(inspect.signature(spc.sum))

# %% [markdown]
# It also registers the method as a service, which means you should not call the method directly.
# instead you should get a service id and the service the container:

# %%
service_id = apps.autoid(spc.sum)  # or apps.autoid(SimplePipelineContainer.sum)
p1 = spc.get(service_id)

# %% [markdown]

# Let's look at the pipeline:

# %%
print("Pipeline input ports:", p1.inputs)
print("Pipeline output ports:", p1.outputs)

app.display(p1)

# %% [markdown]

# Run the pipeline:

# %%
outputs = app.run(
    p1,
    inputs={
        "a": 1.0,
        "b": 2.0,
    },
)

# %% [markdown]

# Print the outputs:

# %%
for k in outputs:
    print(f"{k}: {outputs[k]}")
