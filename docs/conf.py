# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../src')) # Point to the src directory

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pyobuparse'
copyright = '2024, The pyobuparse Authors' # Placeholder, update as needed
author = 'The pyobuparse Authors' # Placeholder

# Attempt to get version from setuptools_scm, fallback otherwise
try:
    from importlib.metadata import version
    release = version('pyobuparse')
    # The short X.Y version
    version = '.'.join(release.split('.')[:2])
except Exception:
    # Fallback if package not installed or setuptools_scm fails during doc build without install
    try:
        import toml
        with open("../pyproject.toml", "r") as f:
            pyproject_data = toml.load(f)
        release = pyproject_data.get("tool", {}).get("setuptools_scm", {}).get("fallback_version", "0.0.0")
        version = '.'.join(release.split('.')[:2])
    except Exception:
        release = '0.0.0'
        version = '0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',  # Include documentation from docstrings
    'sphinx.ext.napoleon', # Support for NumPy and Google style docstrings
    'sphinx.ext.intersphinx', # Link to other projects' documentation
    'sphinx.ext.viewcode', # Add links to source code
    'sphinx.ext.githubpages', # Helps with GitHub Pages deployment
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
# html_theme = 'sphinx_rtd_theme' # Alternative theme
# html_static_path = ['_static'] # Commented out to prevent warning if _static doesn't exist

# -- Intersphinx configuration ---------------------------------------------
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# -- Autodoc configuration -------------------------------------------------
autodoc_member_order = 'bysource' # Order members by source order
autodoc_default_options = {
    'members': True,
    'undoc-members': True, # Show members with no docstring (useful for finding gaps)
    'show-inheritance': True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
