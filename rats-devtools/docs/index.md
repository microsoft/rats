# rats-devtools

The `rats-devtools` component is used to make convenient maintenance and development tooling
specifically for this project. The expectation is that the commands in this component are executed
from the root of the project. We use `pipx` to install the commands into the root `bin` directory
and we suffix them with `.pipx` in order to avoid conflicts with the commands when we are
developing from within the component itself. The `bin/rats-devtools.setup` script should help you
run the necessary commands with proper `pipx` options. Commands installed with `pipx` are not
checked into the repository because they are specific to your workstation.

```bash
cd rats
direnv allow .
rats-devtools.setup
```

If you're making changes to the `rats-devtools` component, you will need to run
`rats-devtools.setup` when certain changes are made to `pyproject.toml`, so it's a good idea to run
this command occasionally to make sure the environment isn't in a stale state.

You can configure shell-completion for the duration of your session with the command below:

``` bash
eval "$(_RATS_DEVTOOLS_PIPX_COMPLETE=zsh_source rats-devtools.pipx)"
```

The commands in this component are also used by our CI pipelines, so will give you a good way
to validate your changes before submitting a pull request.

## mkdocs-serve

Use this command to develop the documentation across the project. It handles combining the markdown
from each component and watching it for changes using `mkdocs serve`. Once running, the
documentation should be available at http://localhost:8000/. Changes to any markdown file will be
auto detected, and your local site will be updates with the latest build.

```bash
rats-devtools.pipx mkdocs-serve
INFO    -  Building documentation...
INFO    -  Cleaning site directory
…
```

## build-jupytext-notebooks

Looks for *.py files under the components' docs/_jupytext_tutorials folders, and converts each one
of them into a *.md notebook under the dos/notebooks.  The file names are expected to have the
format `#_tutorial_title.py` where `#` is an integer, unique within the whole project.  For example
`001_independent_pipelines.py`.

Currently enabled for rats-processors and rats-examples-sklearn.  To enable for other components,
edit the components list in `rats.devtools._commands.build_jupytext_notebooks`. and add `jupytext`
and `nbconvert` to the component's `pyproject.toml` in section
`tool.poetry.group.docs.dependencies`.

The notebooks from the different containers will be collected into a single project level
`Tutorial Notebooks` section.  The order of the tutorials within the section will be determined by
their original file names, hence the requirement for the file names to start with a unique integer.

## build-api-docs

Uses `sphinx` to generate the API Reference documentation for each component in this project,
and pulls them into the docs directories for `mkdocs` to pick up. You can run this command
occasionally when working on docstrings in code, and your local documentation site will be
kept up to date for you to review.

```bash
rats-devtools.pipx build-api-docs
Creating file /rats/rats-pipelines/dist/sphinx-apidoc/rats.app.rst.
Creating file /rats/rats-pipelines/dist/sphinx-apidoc/rats.app_api.rst.
Creating file /rats/rats-pipelines/dist/sphinx-apidoc/rats.examples.rst.
Creating file /rats/rats-pipelines/dist/sphinx-apidoc/rats.examples.io2.rst.
…
```
