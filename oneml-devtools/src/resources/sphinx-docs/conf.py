# -- Project information -----------------------------------------------------
project = "oneml"
copyright = "Us"
author = "The OneML Team"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",  # main extension for generating from docstrings
    "sphinx.ext.autosummary",  # adds summary tables
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",  # not sure this one works with the markdown builder
    # The `sphinx_autodoc_typehints` extension must be loaded AFTER `sphinx.ext.napoleon`.
    "sphinx_autodoc_typehints",
    "sphinx_markdown_builder",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = []

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

always_document_param_types = True

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "class"
autodoc_class_signature = "separated"
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures
