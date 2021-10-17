"""
Configuration file for rendering the documentation.

This folder contains the documentation source files that are to be
rendered as a static web site by the documentation generator Sphinx.
The rendering process is configured by this very script and would be
triggered when running  `sphinx-build . output` on the command line.
The rendered HTML then ends up in the `output` folder, wherein
`index.html` is the start page.

The documentation source comprises the `.md` files here, of which
`index.md` maps to the start page, as well as the doc-strings in the
package's source code for the API documentation. The Markdown parser
for `.md` files is MyST. For doc-strings it is CommonMark, which
supports basic text formating, but no advanced features such as cross
references.
"""

########################################
# Dependencies                         #
########################################

import commonmark                      # Markdown parser
from unittest.mock import MagicMock    # mock imports
import sys                             # system specifics
from pathlib import Path               # file-system path

extensions = [
    'myst_parser',                     # Accept Markdown as input.
    'sphinx.ext.autodoc',              # Get documentation from doc-strings.
    'sphinx.ext.autosummary',          # Create summaries automatically.
    'sphinx.ext.viewcode',             # Include highlighted source code.
    'sphinx.ext.intersphinx',          # Support short-hand web links.
]

# Mock external dependencies so they are not required at build time.
for package in ('jpype', 'jpype.types', 'jpype.imports', 'numpy'):
    sys.modules[package] = MagicMock()

# Add the project folder to the module search path.
main = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(main))

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
master_doc = 'index'                   # start page
nitpicky   = True                      # Warn about missing references?

# Code documentation
autodoc_default_options = {
    'members':       True,             # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}
autosummary_generate = False           # Stub files are created by hand.
add_module_names = False               # Don't prefix members with module name.

# Short-hand web links
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


########################################
# Doc-strings                          #
########################################

def docstring(app, what, name, obj, options, lines):
    """Converts doc-strings from (CommonMark) Markdown to reStructuredText."""
    md  = '\n'.join(lines)
    ast = commonmark.Parser().parse(md)
    rst = commonmark.ReStructuredTextRenderer().render(ast)
    lines.clear()
    lines += rst.splitlines()


def setup(app):
    """Sets up customized text processing."""
    app.connect('autodoc-process-docstring', docstring)
