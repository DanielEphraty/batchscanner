# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os, sys
sys.path.insert(0, os.path.abspath("../src/"))
import batchscanner

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Batchscanner'
copyright = '2023, Daniel Ephraty'
author = 'Daniel Ephraty'
release = batchscanner.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.autodoc',
	'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
	'sphinx_rtd_theme',
    ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# --- Autodoc options ----------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

autodoc_default_options = {
	'members': True,
	'member-order': 'groupwise',
	'special-members': '__init__',
	'exclude-members': '__weakref__',
}

autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
