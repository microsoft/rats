This folder contains the source files for the notebooks in ../tutorial_notebooks.

The source files should be *.py files in jupytext `percent` format, where notebook cells are
deliniated with `# %%`.

The generated per-component tutorial_notebooks folders are later merged into a `Tutorial Notebooks`
section in the project's docs page.

The name of each *.py should be underscore deliniated, starting with an integer.  The integer
determines  the notebooks order in the project's `Tutorial Notebooks` section, and therefore should
be unique across all tutorial notebooks in the project.  The rest of the file name becomes the
title of the notebook.
