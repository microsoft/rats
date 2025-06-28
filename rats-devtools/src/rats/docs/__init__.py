"""
Create the best documentation solution for your project.

This module provides a `rats-docs` command that helps manage documentation in monorepos by
combining generated api docs with markdown files into a single site generated with
[MkDocs](https://www.mkdocs.org/).

We don't plan on enhancing the features of the documentation tooling outside of using standard
mkdocs plugins. Teams working in single-component repositories should be able to author
documentation using the standard `mkdocs build` and `mkdocs serve` commands. In monorepos, our
tools help enable cross-referencing and generate a single site that allows us to search across all
components instead of publishing an isolated documentation site for each component. We try to
accomplish this as a small command proxy that inserts default arguments to the underlying `mkdocs`
command.

!!! note
    Previously, this module would copy original markdown files, and symlink directories during the
    build process to unify the docs across components. However, over time, we've found solutions
    that eliminate these custom operations, making the `rats-docs` commands much simpler, and
    making it easy to get the same output when using `mkdocs` commands directly.

## Structure

We structure our documentation site such that each component is as self contained as possible, each
containing a dedicated `docs` directory. These component docs are then merged with a `docs` folder
found at the root of the repository, where authors can create tutorials and other types of content
that might combine component features to build comprehensive examples. The root docs directory uses
symlinks to the individual component docs, and `mkdocs` is only made aware of the root docs.

We can look at the structure of the `rats` repo as an example:

```bash hl_lines="5-11 19-22 35"
.
├── bin
│   ├── rats-docs
│   ├── …
├── docs # (1)
│   ├── css
│   │   └── extra.css
│   ├── images
│   │   ├── favicon.ico
│   │   └── logo.png
│   └── index.md
├── rats
│   ├── docs
│   │   └── index.md
│   ├── README.md
│   └── src
│       └── rats
├── rats-apps
│   ├── docs # (2)
│   │   ├── index.md
│   │   ├── …
│   │   └── rats.runtime.md
│   ├── README.md
│   ├── src
│   │   ├── rats
│   │   ├── rats_e2e
│   │   └── rats_resources
│   └── test
│       └── rats_test
├── rats.code-workspace
├── rats-devtools
│   ├── docs
│   │   ├── index.md
│   │   ├── …
│   │   └── rats.docs.md # (3)
│   ├── README.md
│   ├── src
│   │   ├── rats
│   │   ├── rats_e2e
│   │   └── rats_resources
│   └── test
│       ├── rats_test
│       └── rats_test_resources
└── README.md -> docs/index.md
```

1.  :man_raising_hand: The root documentation can contain an introduction to the project and
    provide links to component pages.
2.  :man_raising_hand: Components contain their own `docs` directory. We symlink this directory
    such that the `rats-apps` documentation will be at `/rats-apps/`.
3.  :man_raising_hand: This page is part of `rats-devtools` and will be built as if it was found
    at `docs/rats-devtools/rats.docs.md`.

## CLI

In CI Pipelines, the `rats-docs build` command will generate the documentation site and place it in
the `dist/site` directory of your devtools component—the component in your repo that contains your
`mkdocs.yaml`, and has `rats-devtools` installed. The generated docs site can be deployed to
[Github Pages](https://pages.github.com/).

```
$ rats-docs build
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /…/rats/rats-devtools/dist/site
INFO    -  Documentation built in 2.03 seconds
```

Locally, run `rats-docs serve` to make the documentation available at
[http://127.0.0.1:8000/](http://127.0.0.1:8000/). Just like `mkdocs serve`, the site will
automatically rebuild after any detected changes.

```
$ rats-docs serve
INFO    -  Building documentation...
INFO    -  Cleaning site directory
INFO    -  Documentation built in 1.92 seconds
INFO    -  [22:58:02] Watching paths for changes: 'dist/docs', 'dist/mkdocs.yaml',
            '/…/rats/rats-apps/src', 'src', 'mkdocs.yaml'
INFO    -  [22:58:02] Serving on http://127.0.0.1:8000/
INFO    -  [22:58:07] Browser connected: http://127.0.0.1:8000/
INFO    -  [23:06:03] Detected file changes
INFO    -  Building documentation...
INFO    -  Documentation built in 2.08 seconds
INFO    -  [23:06:05] Reloading browsers
INFO    -  [23:06:24] Browser connected: http://127.0.0.1:8000/
```

!!! note
    `rats-docs serve` and `rats-docs build` are simply using the `mkdocs` cli after, and you can
    provide arguments to the underlying command separated by a double dash `--`. You can see the
    entire list of options by running `rats-docs serve -- --help`, which should be equivalent to
    running `mkdocs serve --help`.

    ```
    $ rats-docs serve -- --dev-addr "127.0.0.1:8181"
    INFO    -  Building documentation...
    INFO    -  Cleaning site directory
    INFO    -  Documentation built in 2.73 seconds
    …
    INFO    -  [14:42:00] Serving on http://127.0.0.1:8181/
    ```

## Configuration

[rats.docs.AppConfigs][] contains any configurable aspects of the `rats-docs` application. Register
a [rats.apps.ContainerPlugin][] to the `rats.docs` python entry-point, then define providers for
the configuration values needing updates.

=== "pyproject.toml"
    ```toml
    [project.entry-points."rats.docs"]
    "rats.example" = "rats.example:PluginContainer"
    ```
=== "src/rats/example/_plugin.py"
    ```python
    from rats import apps, docs


    class PluginContainer(apps.Container, apps.PluginMixin):
        @apps.service(docs.AppConfigs.DOCS_COMPONENT_NAME)  # (1)
        def _docs_component(self) -> str:
            return "my-docs-component"  # (2)
    ```

    1.  By default, we assume your repo has a component with `devtools` in the name, and we assume
        this is the component that should run `mkdocs`. The default can be replaced if it doesn't
        meet your needs.
    2.  We set the "my-docs-example" component as the one where mkdocs is installed and configured.
"""

from ._app import AppConfigs, Application, main

__all__ = [
    "AppConfigs",
    "Application",
    "main",
]
