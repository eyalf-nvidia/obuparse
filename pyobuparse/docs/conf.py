import os
import sys
sys.path.insert(0, os.path.abspath('../../src')) # Point to 'src' directory

# -- Project information -----------------------------------------------------
project = 'PyObuParse'
copyright = '2024, Google' # Updated
author = 'Google' # Updated

# Attempt to get version from the package itself
try:
    from pyobuparse import __version__ as release
except ImportError:
    release = '0.1.0' # Fallback version

version = '.'.join(release.split('.')[:2]) # Short X.Y version

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',      # Include documentation from docstrings
    'sphinx.ext.napoleon',     # Support for Google and NumPy style docstrings
    'sphinx.ext.intersphinx',  # Link to other projects' documentation
    'sphinx.ext.viewcode',     # Add links to source code from documentation
    'sphinx.ext.todo',         # Support for todo items
    # 'sphinx_rtd_theme',      # Uncomment if you want to use ReadTheDocs theme
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# html_theme = 'sphinx_rtd_theme' # Uncomment for ReadTheDocs theme
html_theme = 'alabaster' # Default theme
html_static_path = ['_static']
# html_logo = "_static/logo.png" # If you have a logo

# -- Options for intersphinx extension ---------------------------------------
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True

# -- Autodoc options ---------------------------------------------------------
autodoc_member_order = 'bysource'
# autodoc_default_options = {
#     'members': True,
#     'member-order': 'bysource',
#     'special-members': '__init__',
#     'undoc-members': True,
#     'exclude-members': '__weakref__'
# }

# -- Napoleon settings (if using Google/NumPy docstrings) --------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False # Or True if you prefer NumPy style
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
