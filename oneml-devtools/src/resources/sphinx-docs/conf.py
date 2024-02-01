# -- Project information -----------------------------------------------------

project = "oneml"
copyright = "Us"
author = "The OneML Team"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
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

# remove full module name from doc
add_module_names = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'sphinx_material'
# html_theme_path = sphinx.html_theme_path()
# html_context = sphinx.get_html_context()
html_show_sourcelink = False
html_sidebars = {
    "**": ["logo-text.html", "searchbox.html", "globaltoc.html"]
}

html_title = "oneml"
html_short_title = "oneml"
# These are copied from docs/images/* by the sphinx-build CLI command
html_logo = "logo.png"
html_favicon = "favicon.ico"

html_theme_options = {

    # Set the name of the project to appear in the navigation.
    "nav_title": "oneml",
    "repo_url": "https://github.com/microsoft/oneml",
    "repo_name": "oneml",

    # Set the color and the accent color
    "color_primary": "teal",
    "color_accent": "light-blue",

    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": -1,
    # If False, expand all TOC entries
    "globaltoc_collapse": True,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": True,
    "master_doc": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
always_document_param_types = True
