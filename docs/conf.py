# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the src directory to the path for autodoc
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cysox'
copyright = '2025, Shakeeb Alireza'
author = 'Shakeeb Alireza'
release = '0.1.1'
version = '0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    # 'myst_parser',
]

# MyST parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Source file suffixes
source_suffix = {
    '.rst': None,
    # '.md': 'myst_parser.sphinx_',
}

# -- Options for autodoc -----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}

# Don't skip __init__ methods
autodoc_class_signature = 'separated'

# -- Options for Napoleon (Google/NumPy docstrings) --------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for intersphinx -------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]

pygments_style = 'sas'

# Theme options
# html_theme_options = {
#     "light_css_variables": {
#         "color-brand-primary": "#4051b5",
#         "color-brand-content": "#4051b5",
#     },
#     "dark_css_variables": {
#         "color-brand-primary": "#7c8aff",
#         "color-brand-content": "#7c8aff",
#     },
# }

html_title = "cysox"
html_short_title = "cysox"

# -- Options for autosummary -------------------------------------------------

autosummary_generate = True
