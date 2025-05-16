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

from mph import meta
from pathlib import Path
import sys


# Add custom Sphinx extensions to module search path.
here = Path(__file__).parent
sys.path.insert(0, str(here/'extensions'))

# Load Sphinx extensions.
extensions = [
    'myst_parser',                     # Markdown support in documents
    'myst_docstring',                  # Markdown support in doc-strings
    'myst_summary',                    # Markdown support in summary tables
    'sphinx.ext.viewcode',             # additional [source] links
    'sphinx.ext.intersphinx',          # inter-project cross-references
]

# Meta information
project = meta.name
version = meta.version
release = version

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
autodoc_typehints = 'none'             # Rendering type hints doesn't work.
autosummary_generate = False           # Stub files are created by hand.
add_module_names = False               # Drop module prefix from signatures.

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
