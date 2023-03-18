"""
Configuration file for rendering the documentation.

This folder contains the documentation source files that are to be
rendered as a static web site by the documentation generator Sphinx.
The rendering process is configured by this very script and would be
triggered when running  `sphinx-build . output` on the command line.
The rendered HTML then ends up in the `output` folder, wherein
`index.html` is the start page.

The documentation source is written in Markdown. It comprises the `.md`
files here, of which `index.md` maps to the start page, as well as the
doc-strings in the package's source code for the API documentation. The
Markdown parser is MyST. Doc-string support for MyST is added by custom
Sphinx extensions.
"""

########################################
# Dependencies                         #
########################################

import sys                             # system specifics
from pathlib import Path               # file-system path
from unittest.mock import MagicMock    # mock imports

# Modify module search path.
here = Path(__file__).absolute().parent
sys.path.insert(0, str(here.parent))
sys.path.insert(0, str(here/'extensions'))

# Load Sphinx extensions.
extensions = [
    'myst_parser',                     # Accept Markdown as input.
    'myst_docstring',                  # Get documentation from doc-strings.
    'myst_summary',                    # Create summaries automatically.
    'sphinx.ext.viewcode',             # Include highlighted source code.
    'sphinx.ext.intersphinx',          # Support short-hand web links.
]

# Mock external dependencies so they are not required at build time.
for package in ('jpype', 'jpype.imports', 'numpy'):
    sys.modules[package] = MagicMock()

# Make the package's meta data available.
from mph import meta


########################################
# Configuration                        #
########################################

# Meta information
project   = meta.title
author    = meta.author
copyright = meta.copyright
version   = meta.version
release   = version

# Web site
html_title   = f'{project} {version}'  # document title
html_logo    = 'images/logo.svg'       # project logo
html_favicon = 'images/logo.svg'       # browser icon

# Source parsing
root_doc = 'index'                     # start page
nitpicky = True                        # Warn about missing references?
exclude_patterns = ['ReadMe.md']       # Ignore ReadMe in this folder here.

# Code documentation
autodoc_default_options = {
    'members':       True,             # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}
autosummary_generate = False           # Stub files are created by hand.
add_module_names = False               # Don't prefix members with module name.

# External link targets
intersphinx_mapping = {
    'python': ('https://docs.python.org/3',    None),
    'numpy':  ('https://numpy.org/doc/stable', None),
}

# Rendering options
myst_heading_anchors = 2               # Generate link anchors for sections.
html_copy_source     = False           # Copy documentation source files?
html_show_copyright  = False           # Show copyright notice in footer?
html_show_sphinx     = False           # Show Sphinx blurb in footer?

# Rendering style
html_theme          = 'furo'           # custom theme with light and dark mode
pygments_style      = 'friendly'       # syntax highlight style in light mode
pygments_dark_style = 'stata-dark'     # syntax highlight style in dark mode
html_static_path    = ['style']        # folders to include in output
html_css_files      = ['custom.css']   # extra style files to apply
