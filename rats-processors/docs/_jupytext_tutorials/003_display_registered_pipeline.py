# %% [markdown]
# ## Tutorial notebook: inspecting and running a registered pipeline.

# %%
import rats.processors as rp

# %%
app = rp.NotebookApp()
# %% [markdown]

# List all the registered pipelines

# %%
eps = app.executable_pipelines()
list(eps)

# %% [markdown]

# Choose one of the registered pipelines.  Print the documentation.

# %%
ep = eps["examples.untyped_simple_pipeline"]
print(ep.doc)

# %% [markdown]

# Get the pipeline object.

# %%
p = ep.provider()

# %% [markdown]

# Inpect it: print it's input and output ports, and display its graph.
#
# You might get an error message asking you to install Graphviz. If you do, install it and rerun.

# %%
print("Pipeline input ports:", p.inputs)
print("Pipeline output ports:", p.outputs)

app.display(p)
# %% [markdown]

# Run the pipeline with some inputs
# (remember this is a fake training pipeline, it just constructs some message.)

# %%
outputs = app.run(
    p,
    inputs={
        "model_type": "linear",
        "num_layers": 20,
        "url": "https://something",
    },
)
# %% [markdown]

# Print the outputs (keyed by port name)

# %%
print(outputs["message"])

# %%
