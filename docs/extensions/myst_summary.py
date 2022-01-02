"""MyST-compatible drop-in replacement for Sphinx's Autosummary extension."""
__version__ = '0.1.0'

# This extension only overrides the Autosummary method that creates the
# summary table. The changes relative to the original code are minimal.
# Though it is possible some reST-specific content generation was
# overlooked elsewhere in Autosummary's code base. The stub generation
# was ignored. We would have to create .md files instead of .rst.

import sphinx
from sphinx.ext import autosummary
import docutils


class Autosummary(autosummary.Autosummary):
    """Extends the `autosummary` directive provided by Autosummary."""

    def get_table(self, items):
        """
        Reimplements the generation of the summary table.

        This new method returns Docutils nodes containing MyST-style
        object references instead of standard Sphinx roles. It simply
        regenerates the content. (It may also be possible to call the
        method of the parent class and convert the syntax with a
        regular expression after it's been generated.)
        """
        table_spec = sphinx.addnodes.tabular_col_spec()
        table_spec['spec'] = r'\X{1}{2}\X{1}{2}'

        table = autosummary.autosummary_table('')
        real_table = docutils.nodes.table('', classes=['longtable'])
        table.append(real_table)
        group = docutils.nodes.tgroup('', cols=2)
        real_table.append(group)
        group.append(docutils.nodes.colspec('', colwidth=10))
        group.append(docutils.nodes.colspec('', colwidth=90))
        body = docutils.nodes.tbody('')
        group.append(body)

        def append_row(*column_texts: str) -> None:
            row = docutils.nodes.row('')
            (source, line) = self.state_machine.get_source_and_line()
            for text in column_texts:
                node = docutils.nodes.paragraph('')
                vl = docutils.statemachine.StringList()
                vl.append(text, f'{source}:{line:d}:<autosummary>')
                with sphinx.util.docutils.switch_source_input(self.state, vl):
                    self.state.nested_parse(vl, 0, node)
                    try:
                        if isinstance(node[0], docutils.nodes.paragraph):
                            node = node[0]
                    except IndexError:
                        pass
                    row.append(docutils.nodes.entry('', node))
            body.append(row)

        for (name, sig, summary, real_name) in items:
            if 'nosignatures' not in self.options:
                item = ('{py:obj}' + f'`{name} <{real_name}>`\\ '
                        + sphinx.util.rst.escape(sig))
            else:
                item = '{py:obj}' + f'`{name} <{real_name}>`'
            append_row(item, summary)

        return [table_spec, table]


def setup(app):
    """
    Sets up the extension.

    Sphinx calls this function if the user named the extension in `conf.py`.
    It then sets up the Autosummary extension that ships with Sphinx  and
    overrides whatever necessary to produce Markdown to be parsed by MyST
    instead of reStructuredText parsed by Sphinx/Docutils.
    """
    app.setup_extension('sphinx.ext.autosummary')
    app.add_directive('autosummary', Autosummary, override=True)
    return {'version': __version__, 'parallel_read_safe': True}
