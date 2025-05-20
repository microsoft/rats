# introduction

The `rats-devtools` component provides a suite of tools to automate and streamline the development
workflow for any application. It offers commands for tasks such as CI pipeline checks,
container image building, documentation generation, and other essential development operations that
support, but are not directly part of, your product. While originally developed for this project,
`rats-devtools` is now designed for general use and can help teams enforce best practices and
maintain high-quality development environments across different projects.

Typically, the commands provided by this component are installed repo-wide, and are able to support
both monorepos, and single-component code bases. The tools for the development of `rats` components
can be installed with the `rats.setup` script found in the `bin/` folder.

```bash
cd rats
direnv allow .
rats.setup
```

You can configure shell-completion for the duration of your session with the commands below:

``` bash
eval "$(_RATS_AML_COMPLETE=zsh_source rats-aml)"
eval "$(_RATS_CI_COMPLETE=zsh_source rats-ci)"
eval "$(_RATS_DOCS_COMPLETE=zsh_source rats-docs)"
eval "$(_RATS_EZ_COMPLETE=zsh_source rats-ez)"
```

The commands in this component are also used by our CI pipelines, so will give you a good way
to validate your changes before submitting a pull request.

## rats-docs

The [rats.docs][] module provides the `rats-docs` cli command, used to pull together documentation
from across the code base, and compile it into a single static site. We use
[MkDocs](https://www.mkdocs.org/) packages, along with a handful of plugins, to combine markdown
files with generated API documentation into a single, easily searchable, documentation site.

### rats-docs serve

Use this command to develop the documentation across the project. It handles combining the markdown
from each component and watching it for changes using `mkdocs serve`. Once running, the
documentation should be available at http://localhost:8000/. Changes to any markdown file will be
auto detected, and your local site will be updates with the latest build.

```bash
rats-docs mkdocs-serve
INFO    -  Building documentation...
INFO    -  Cleaning site directory
…
```
