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
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################

import commonmark                      # Markdown parser
from unittest.mock import MagicMock    # mock imports
import sys                             # system specifics
from pathlib import Path               # file-system path

extensions = [
    'sphinx_rtd_theme',                # Register Read-the-Docs theme.
    'myst_parser',                     # Accept Markdown as input.
    'sphinx.ext.autodoc',              # Get documentation from doc-strings.
    'sphinx.ext.autosummary',          # Create summaries automatically.
    'sphinx.ext.viewcode',             # Add links to highlighted source code.
    'sphinx.ext.mathjax',              # Render math via JavaScript.
]

# Add the project folder to the module search path.
main = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(main))

# Mock external dependencies so they are not required at build time.
autodoc_mock_imports = ['jpype', 'numpy']
for package in ('jpype', 'jpype.types', 'jpype.imports', 'numpy'):
    sys.modules[package] = MagicMock()

# Import package to make meta data available.
import mph as meta


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
    """Configure customized text processing."""
    app.connect('autodoc-process-docstring', docstring)


########################################
# Configuration                        #
########################################

# Meta information
project   = meta.__title__
version   = meta.__version__
release   = meta.__version__
date      = meta.__date__
author    = meta.__author__
copyright = meta.__copyright__
license   = meta.__license__

# Source parsing
master_doc = 'index'                   # start page
nitpicky   = True                      # Warn about missing references?

# Code documentation
add_module_names = False               # Don't prefix members with module name.
autodoc_default_options = {
    'members':       True,             # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}

# Output style
html_theme       = 'sphinx_rtd_theme'  # Use the Read-the-Docs theme.
pygments_style   = 'trac'              # syntax highlighting style
html_static_path = ['style']           # folders to include in output
html_css_files   = ['custom.css']      # extra style files to apply

# Output options
myst_heading_anchors = 2               # Generate link anchors for sections.
html_copy_source     = False           # Copy documentation source files?
html_show_copyright  = False           # Show copyright notice in footer?
html_show_sphinx     = False           # Show Sphinx blurb in footer?
