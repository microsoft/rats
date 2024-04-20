# rats-processors




In you python project or Jupyter notebook, you can compose a pipeline as follows:

```python
from typing import NamedTuple

import pandas as pd
from rats.apps import PipelineContainer
from rats.processors import CombinedPipeline, ExecutablePipeline, task, pipeline


class DataOut(NamedTuple):
    data: pd.DataFrame


class MyContainer(PipelineContainer):
    @task
    def load_data(self) -> DataOut:
        return DataOut(data=pd.read_csv("data.csv"))

    @task
    def train_model(self, data: pd.DataFrame):
        return {"model": "trained"}

    @pipeline
    def my_pipeline(self) -> ExecutablePipeline:
        load_data = self.load_data()
        train_model = self.get(train_model)
        return self.combine(
            pipelines=[load_data, train_model],
            dependencies=(train_model.inputs.data << load_data.outputs.data),
        )
```
and run it like this:

```python
container = MyContainer()  # initialize your container
p = container.get("my_pipeline")  # public method to get a service from a container
container.draw(p)
container.run(p)
```
