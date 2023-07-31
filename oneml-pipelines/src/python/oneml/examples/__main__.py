from oneml.app import OnemlApp
from oneml.examples._pipeline import OnemlExamplePipelines

app = OnemlApp.default()
app.run(lambda: print("hello, world! this command was run with an inline executable."))

app.run_pipeline(OnemlExamplePipelines.HELLO_WORLD)
app.run_pipeline(OnemlExamplePipelines.HELLO_WORLD)
print("done running my pipelines :)")
