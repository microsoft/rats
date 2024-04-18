# Research Analysis Tools (rats)

[![Main](https://github.com/microsoft/rats/actions/workflows/main.yaml/badge.svg)](https://github.com/microsoft/rats/actions/workflows/main.yaml)
[![codecov](https://codecov.io/gh/microsoft/rats/graph/badge.svg?token=hcpBAa587E)](https://codecov.io/gh/microsoft/rats)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/microsoft/rats/main.svg)](https://results.pre-commit.ci/latest/github/microsoft/rats/main)
[![Checked with pyright](https://microsoft.github.io/pyright/img/pyright_badge.svg)](https://microsoft.github.io/pyright/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![PyPI - Version](https://img.shields.io/pypi/v/rats-pipelines)](https://pypi.org/project/rats-pipelines/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rats-pipelines)](https://pypi.org/project/rats-pipelines/)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/rats-pipelines)](https://pypi.org/project/rats-pipelines/)


Rats is a collection of tools to help researchers define and run experiments.
It is designed to be a modular and extensible framework currently supporting building and
running pipelines, integrating configs and services.

**NOTE**: This project is in the early stages of development and is not yet ready for use.


## Documentation
https://microsoft.github.io/rats


## Getting started

Install the latest version of rats from PyPI:

```bash
# With pip3.
pip3 install rats-apps rats-pipelines rats-processors

# With poetry.
poetry add rats-apps rats-pipelines rats-processors

# With uv.
uv pip install rats-apps rats-pipelines rats-processors

# With pipenv.
pipenv install rats-apps rats-pipelines rats-processors
```

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


## Components


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
