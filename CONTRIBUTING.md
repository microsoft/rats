# :mountain: Contributing

This project welcomes contributions and suggestions. Most contributions require you to
agree to a Contributor License Agreement (CLA) declaring that you have the right to,
and actually do, grant us the rights to use your contribution. For details, visit
<https://cla.microsoft.com>.

When you submit a pull request, a CLA-bot will automatically determine whether you need
to provide a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the
instructions provided by the bot. You will only need to do this once across all repositories using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## :space_invader: Codespaces

We provide a configured devcontainer for you to use with this project.
You can create a container image with all the necessary dependencies,
and use it for remote development in a remote node with [GitHub Codespaces](https://docs.github.com/en/codespaces).

:point_right: Click below to clone or fork this repository automatically and start developing:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/microsoft/rats)

## :gear: Devcontainer

Alternatively, you can build a local container directly and use it in VSCode and/or
PyCharm without developing in a remote node or setting up a local environment.

Learn about [Devcontainers](https://containers.dev/).
Requires [Docker](https://www.docker.com/get-started/) installed on your local machine.

:point_right: Follow instructions for [VSCode](https://code.visualstudio.com/docs/devcontainers/tutorial)
and/or [PyCharm](https://www.jetbrains.com/help/pycharm/connect-to-devcontainer.html).

## :computer: Local development

The only required dependency for local development is [uv](https://docs.astral.sh/uv/getting-started/installation/).

We recommend installing some extra dependencies to improve the development experience, e.g.,
[direnv](https://direnv.net/), [GitHub CLI](https://cli.github.com/), [pre-commit](https://pre-commit.com/) and
[commitizen](https://commitizen-tools.github.io/commitizen/).

## :hammer_and_wrench: Description of development tools

This project uses the following tools to facilitate the development experience:

* [uv](https://docs.astral.sh/uv/) for Python management, dependency management, virtual environments and
packaging, i.e., makes your code readily importable!
* [ruff](https://github.com/astral-sh/ruff) for formatting and linting: helps you write clean and uniform code for better consistency (and it's fast!).
* [pytest](https://docs.pytest.org/en/stable/) for testing: ensures your code is working as expected!
* [pyright](https://github.com/microsoft/pyright) for static annotations: helps identify simple errors, but more importantly,
makes your code more readable!
* [codespell](https://github.com/codespell-project/codespell) for spell checking: pinpoints spelling errors across code and documents.
* [CI workflows](https://en.wikipedia.org/wiki/Continuous_integration): automates validation when you submit a PR or merge to `main` branch.
* [pre-commit](https://pre-commit.com/) for quick validation checks and fixes before committing.
* [commitizen](https://commitizen-tools.github.io/commitizen/)
for writing [conventional commits](https://www.conventionalcommits.org/), to help write better commit messages
and track changes through [time](https://github.com/microsoftokie-doh/blob/main/CHANGELOG.md).
