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


## Documentation
https://microsoft.github.io/rats


## Components

### rats-apps
A light package containing the interfaces and tools to organize your code in a modular way.
It provides the mechanisms to define _services_ (a.k.a., general purpose objects) and _containers_
(classes containing service providers).
These _containers_ are then added to a general app as plugins providing an entry point to a whole
ecosystem of general _services_.

### rats-pipelines

A package to define and run pipelines of _nodes_ (computational tasks) and _edges_
(node dependencies or data dependencies).
It provides a low-level API to define pipeline execution, task execution and IO management.
It also provides a high level API to orchestrate running a pipeline locally or in a distributed
environment.


### rats-processors

A package to create and compose pipelines in a higher level API, where _processors (classes
or unbound methods) are mapped into _pipeline nodes_, _node ports_ are inferred from the
_processors_ signature, and _edges_ are created by connecting the _node ports_ inputs and outputs.
Pipelines defined this way are immutable objects that can be reused and composed into larger
pipelines.

### rats-devtools

A light component to help with the development of the other components.
It provides a set of tools to generate documentation, run tests, format and lint code and help
in the release process.


## Getting started

Install the latest version of rats from PyPI for any component you want:

```bash
# With pip3.
pip3 install rats-apps rats-apps rats-pipelines rats-processors

# With poetry.
poetry add rats-apps rats-apps rats-pipelines rats-processors

# With uv.
uv pip install rats-apps rats-apps rats-pipelines rats-processors

# With pipenv.
pipenv install rats-apps rats-apps rats-pipelines rats-processors
```

## Development

### Optional system dependencies

We use the following optional dependencies for development:
* [direnv](https://direnv.net/): To manage environment variables and load python virtual environments automatically.
* [pyenv](https://github.com/pyenv/pyenv): To manage python versions.
* [pipx](https://pipxproject.github.io/pipx/): To install python packages in isolated environments.
* [commitizen](https://commitizen-tools.github.io/commitizen/): To help with [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).
* [cz-conventional-gitmoji](https://github.com/ljnsn/cz-conventional-gitmoji): A commitizen plugin that combines gitmoji and conventional commits.
* [pre-commit](https://pre-commit.com/): To run code formatting and linting before committing.

### Required system dependencies

* [poetry](https://python-poetry.org/): To manage package dependencies and virtual environments.
* [python >= 3.10](https://www.python.org/)

For setting up the development environment:

* Clone the repository and cd into it.
* Install the dependencies with poetry:
```bash
cd rats; poetry install; cd -
cd rats-apps; poetry install; cd -
cd rats-devtools; poetry install; cd -
cd rats-pipelines; poetry install; cd -
cd rats-processors; poetry install; cd -
```
* Install `rats-devtools` command (optional):
```bash
pipx install -e rats-devtools  # installs in local environment
```


## Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
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
