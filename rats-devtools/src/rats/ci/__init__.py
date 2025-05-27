"""
Commands for building and validating components.

The `rats-ci` application provides a set of sub-commands that represent common operations done in
the typical CI pipeline. Wrapping the CI logic into a cli application allows us to run these same
checks locally during development, and reproduce any possible issues that fail the CI pipeline,
avoiding a long development loop. The `rats-ci` command can be installed repo-wide in a monorepo,
but the commands should be run from within a component, where the `pyproject.toml` file is located.

When using the `rats-ci` application within a monorepo, we can give developers a common API while
adapting to the different technology choices within any given component.

## CLI

The `rats-ci` command is broken up into `build-image`, `check`, `fix`, `install`, and `test`
groups, which map to one or more default commands that can be customized by users. Any number of
the provided commands can be run in sequence, so `rats-ci fix check test` is often used as a quick
way to fix any linting errors automatically, when possible; running the linting and typing checks,
as configured by the component being checked; and any unit tests, using `pytest` by default.

```
Usage: rats-ci [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  commands used during ci/cd

Options:
  --help  Show this message and exit.

Commands:
  build-image  Build a container image of the component.
  check        Run any configured linting & typing checks for the component.
  config       Show information about the configured command groups for active
               component.
  fix          Run any configured auto-formatters for the component.
  install      Install the development environment for the component.
  test         Run any configured tests for the component.
```

## Configuration

!!! info
    The default configuration reflects the tools and options we use when developing rats.
    However, we want the entire development team to use a common set of commands, like
    `rats-ci check` to run linting and other type checking rules, regardless of any differences
    in language or configuration across components. Separating the implementation details from the
    CI/CD concepts allows the team to contribute across a growing code base without needing to
    memorize a new set of development commands; and without needing to force all components to
    follow a very rigid set of commands.

    Apart from configuring each group with the settings below, we can configure all groups in one
    operation using the [rats.ci.AppConfigs.COMMAND_GROUPS][] service.

You can run `rats-ci config` to see the current configuration for the ci commands within your
component. If you haven't modified the defaults, you should see the configuration below.

```
$ cd rats-apps
$ rats-ci config
component: rats-apps
  install
    poetry install
  fix
    ruff check --fix --unsafe-fixes
    ruff format
  check
    ruff format --check
    ruff check
    pyright
  test
    pytest
```

### install

We're currently using [Poetry](https://python-poetry.org/) for dependency management, so the
`rats-ci install` command maps simply to `poetry install` by default. In simple cases, this command
might not be immediately necessary on most projects; but if installing all the development
dependencies in a component requires more than one command, or you have components other than
python packages, you can update the [rats.ci.AppConfigs.INSTALL][] service to define your
installation steps.

### fix

The `rats-ci fix` command tries to make any linting or style fixes possible. Any kind of automated
formatting tools that can remove tedious process for maintaining a common style across the project,
and can avoid failing CI builds for uninteresting reasons that would create a long, annoying
feedback loop. By default, we run `ruff check --fix --unsafe-fixes` and `ruff format`, and expect
the component being fixed to have [ruff](https://docs.astral.sh/ruff/) installed and configured,
as usual. The default behavior can be updated by setting [rats.ci.AppConfigs.FIX][].

### check

Any linting and typing errors that can't be automatically fixed with `rats-ci fix`, can be detected
with `rats-ci check`. We run `ruff format --check`, `ruff check`, and `pyright`, but these defaults
can be changed with the [rats.ci.AppConfigs.CHECK][] service.

### test

We run our test suite with `pytest`, but occasionally register additional commands to run
integration and end-to-end tests. The [rats.ci.AppConfigs.TEST][] service can be provided to change
the configured test suite.

### build-container

The `rats-ci build-container` command builds and pushes a container image based on the value of
the `DEVTOOLS_IMAGE_REGISTRY` and `DEVTOOLS_IMAGE_TAG` environment variables. If
`DEVTOOLS_IMAGE_TAG` is not defined, we use the [rats.projects][] module to calculate a tag based
on the hash of all the files available to the build context. The image push can be disabled by
setting the `DEVTOOLS_IMAGE_PUSH_ON_BUILD=0` environment variable.

```
$ cd rats-apps
$ rats-ci build-image
building docker image: example.azurecr.io/rats-apps:8b79a4344354…
[+] Building 2.5s (14/14) FINISHED
 => [internal] load build definition from Containerfile
 => => transferring dockerfile: 1.41kB
…
 => [1/9] FROM mcr.microsoft.com/mirror/docker/library/ubuntu:24.04
…
 => [9/9] COPY . /opt/rats
 => exporting to image
 => => exporting layers
 => => writing image sha256:2150f859e…
 => => naming to example.azurecr.io/rats-apps:8b79a434…
…
5f70bf18a086: Layer already exists
ef2fe6e1db4c: Pushed
b02f35d52f65: Pushed
…
8b79a4…aa69d: digest: sha256:a2c3356…4c9ca size: 2199
```

!!! info
    For legacy reasons, the `rats-ci build-container` command is not yet configurable in the same
    way the others are, but we hope to address this in a future release.
"""

from ._app import AppConfigs, Application, CiCommandGroups, main

__all__ = [
    "AppConfigs",
    "Application",
    "CiCommandGroups",
    "main",
]
