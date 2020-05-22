"""
Configuration file for rendering the documentation.

This folder contains the documentation source files that are to be
rendered as a static web site by the documentation generator Sphinx.
The rendering process is configured by this very script and would be
triggered by running  `sphinx-build . rendered` on the command line,
no matter the operating system. The rendered HTML then ends up in the
sub-folder `rendered`, where `index.html` is the start page.

The documentation source is comprised of the `.md` files here, of which
`index.md` maps to the start page, as well as the documentation strings
in the package's source code for the API documentation.

All text may use mark-up according to the CommonMark specification of
the Markdown syntax. The Sphinx extension `reCommonMark` is used to
convert Markdown to reStructuredText, Sphinx's native input format.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################

import sphinx_rtd_theme                # Read-the-Docs theme
import recommonmark                    # Markdown extension
import recommonmark.transform          # Markdown transformations
import commonmark                      # Markdown parser
import re                              # regular expressions
import sys                             # system specifics
from unittest.mock import MagicMock    # mock imports
from pathlib import Path               # file-system paths

extensions = [
    'sphinx_rtd_theme',                # Register Read-the-Docs theme.
    'recommonmark',                    # Accept Markdown as input.
    'sphinx.ext.autodoc',              # Get documentation from doc-strings.
    'sphinx.ext.autosummary',          # Create summaries automatically.
    'sphinx.ext.viewcode',             # Add links to highlighted source code.
    'sphinx.ext.mathjax',              # Render math via JavaScript.
]

# Add the project folder to the module search path.
main = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(main))

# Mock external dependencies so they are not required at build time.
autodoc_mock_imports = ['jpype', 'numpy', 'winreg']
for package in ('jpype', 'jpype.types', 'jpype.imports', 'numpy', 'winreg'):
    sys.modules[package] = MagicMock()

# Import package to make meta data available.
import mph as meta


########################################
# Customization                        #
########################################

def convert(text):
    """
    Converts text from Markdown to reStructuredText syntax.

    Also converts the Unicode bullet character (•) to a standard
    list-item marker (*) so that the CommomMark parser recognizes it
    as such — which it regrettably doesn't.
    """
    text = re.sub(r'^([ \t]*)•', r'\1*', text, flags=re.MULTILINE)
    ast = commonmark.Parser().parse(text)
    rst = commonmark.ReStructuredTextRenderer().render(ast)
    return rst


def docstrings(app, what, name, obj, options, lines):
    """Converts Markdown in doc-strings to reStructuredText."""
    md  = '\n'.join(lines)
    rst = convert(md)
    lines.clear()
    lines += rst.splitlines()


def setup(app):
    """Sets up event hooks for customized source processing."""
    app.connect('autodoc-process-docstring', docstrings)
    app.add_config_value('recommonmark_config', {
        'auto_toc_tree_section': 'Contents',
        'enable_math': True,
        'enable_inline_math': True,
        'enable_eval_rst': True,
    }, True)
    app.add_transform(recommonmark.transform.AutoStructify)


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
master_doc         = 'index'           # start page
source_suffix      = ['.md', '.rst']   # valid source-file suffixes
language           = None              # language for auto-generated content
nitpicky           = True              # Warn about missing references?

# Code documentation
default_role       = 'code'            # Back-ticks denote code in reST.
add_module_names   = False             # Don't precede members with module name.
autodoc_default_options = {
    'members':       None,             # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}

# Output style
html_theme       = 'sphinx_rtd_theme'  # Use Read-the-Docs theme.
html_static_path = ['style']           # folders to include in output
html_css_files   = ['custom.css']      # additional style files
pygments_style   = 'trac'              # syntax highlighting style

# Output options
html_copy_source    = False            # Copy documentation source files?
html_show_copyright = False            # Show copyright notice in footer?
html_show_sphinx    = False            # Show Sphinx blurb in footer?
