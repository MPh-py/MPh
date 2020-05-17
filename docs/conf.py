"""
Configuration file for rendering the documentation.

The files in this folder are used to render the documentation of this
package, from its source files, as a static web site. The renderer is
the documentation generator Sphinx. It is configured by this very
script and would be invoked on the command line via, on any operating
system, via `sphinx-build . rendered`. The static HTML then ends up in
the sub-folder `rendered`, where `index.html` is the start page.

The source files are the `.md` files here, where `index.md` maps to
the start page, as well as the documentation string in the package's
source code for the API documentation.

All text may use mark-up according to the CommonMark specification of
the Markdown syntax. The Sphinx extension `recommonmark` is used to
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
import mph as package


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
    """Sets up event hooks for customized text processing."""
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
project   = package.__title__
version   = package.__version__
date      = package.__date__
author    = package.__author__
copyright = package.__copyright__
license   = package.__license__

# Source parsing
master_doc         = 'index'           # start page
source_suffix      = ['.md', '.rst']   # valid source-file suffixes
exclude_patterns   = []                # files and folders to ignore
language           = None              # language for auto-generated content
todo_include_todos = False             # Include "todo" and "todoList"?
nitpicky           = True              # Warn about missing references?

# Code documentation
add_module_names    = False            # Don't precede members with module name.
autodoc_default_options = {
    'members': True,                   # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}

# HTML rendering
html_theme          = 'sphinx_rtd_theme'
html_theme_path     = [sphinx_rtd_theme.get_html_theme_path()]
html_theme_options  = {}
templates_path      = ['layout']       # layout tweaks
html_static_path    = ['style']        # style tweaks
html_css_files      = ['custom.css']   # style sheets
pygments_style      = 'trac'           # syntax highlighting style
html_use_index      = False            # Create document index?
html_copy_source    = False            # Copy documentation source files?
html_show_copyright = False            # Show copyright notice in footer?
html_show_sphinx    = False            # Show Sphinx blurb in footer?
html_favicon        = None             # browser icon
html_logo           = None             # project logo
