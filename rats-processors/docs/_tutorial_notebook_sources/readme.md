This folder contains the source files for the notebooks in ../_tutorial_notebooks.

The source files should be *.py files in jupytext `percent` format, where notebook cells are
deliniated with `# %%`.

The generated notebooks are not automatically exposed in the project's docs page.  To expose a
notebook in the `Tutorial Notebooks` section of a component, add a symbolic link to the notebook's
*.md file in the docs/tutorial_notebooks/ folder of the component, and add the symbolic link to
the .pages file in that folder. Note that the `Tutorial Notebooks` section of a component may
include notebooks built in other components.  See `rats-processors/docs/tutorial_notebooks/` for
an example.
