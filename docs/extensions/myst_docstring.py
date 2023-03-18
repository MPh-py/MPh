"""
MyST-compatible drop-in replacement for Sphinx's Autodoc extension

This extension overrides Autodoc's generation of [domain] directives
so that the syntax is what the MyST Markdown parser expects, instead of
Sphinx's own reStructuredText parser.

Note that this is very much a hack. Ideally, Autodoc would query what
the document's source parser is and generate output accordingly.

[domain]: https://www.sphinx-doc.org/en/master/usage/restructuredtext\
/domains.html
"""
__version__ = '0.2.1'


from sphinx.ext import autodoc


class Documenter(autodoc.Documenter):
    """
    Mix-in to override content generation by `Documenter` class.

    All of Autodoc's documenter classes (for modules, functions, etc.)
    derive from the `Documenter` base class. Two methods are important:
    * The one that adds the directive header, i.e. opens the directive.
    * The one that generates the content, which includes the actual
      doc-string as well as documentation for all child elements, such
      as methods of a class.

    Problem is, reStructuredText directives need never be explicitly
    closed, as scopes are designated by indentation. With MyST, however,
    we have to do just that: add an extra line to close a directive
    previously opened, as indentation itself is not significant per se.

    To make our life at least somewhat easier, we also use an
    undocumented feature of MyST, or perhaps Markdown-it: We can nest
    directives delimited by exactly three back-ticks, ` ``` `, inside
    directives delimited by three tildes, `~~~`. Then indentation *is*
    significant, though we still have to close the directive's scope.
    But at least we don't have to add extra back-ticks on enclosing
    scopes, just so inner scopes don't mess with the delimitation,
    which we would have to do otherwise.

    Ideally, Autodoc would be aware of such structural syntax
    requirements. But it's not. And it doesn't call out to the parser
    anyway, it simply generates reStructuredText no matter what. A
    robust solution would make Autodoc parser-aware, upstream, i.e.
    in Sphinx.
    """

    def add_directive_header(self, sig):
        """Adds the directive header and options."""

        # Defer to super method when not parsing Markdown.
        # Hack. There must be a better way to find out if MyST is the parser.
        parser_is_myst = self.directive.state.__module__.startswith('myst')
        if not parser_is_myst:
            super().add_directive_header(sig)
            return

        # This block is unchanged, just copied from the super method.
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        sourcename = self.get_sourcename()

        # Modify the directive prefix.
        markers = '```' if self.indent else '~~~'
        prefix  = markers + '{' + f'{domain}:{directive}' + '} '

        # Remember we opened this directive.
        if not hasattr(self, 'directives'):
            self.directives = []
        self.directives.append((domain, directive, name, markers))

        # Bail out if we are more than one level deep, which is unexpected.
        if len(self.directives) > 1:
            raise RuntimeError('MyST-Docstring cannot handle this project.')

        # Open the directive. (This block is unchanged.)
        for i, sig_line in enumerate(sig.split("\n")):
            self.add_line('%s%s%s' % (prefix, name, sig_line), sourcename)
            if i == 0:
                prefix = " " * len(prefix)
        if self.options.noindex:
            self.add_line('   :noindex:', sourcename)
        if self.objpath:
            self.add_line('   :module: %s' % self.modname, sourcename)

        # Close directive immediately if it is a module.
        # This approach, of doing that right here, will break certain
        # corners cases, see `ModuleDocumenter.add_directive_header()`
        # in `sphinx.ext.autodoc.__init__.py`.
        if (domain, directive) == ('py', 'module'):
            self.directives.pop()
            self.add_line(markers, sourcename)

    def generate(self, **arguments):
        """Generates documentation for the object and its members."""

        # Defer to super method when not parsing Markdown.
        # Hack. There must be a better way to find out if MyST is the parser.
        parser_is_myst = self.directive.state.__module__.startswith('myst')
        if not parser_is_myst:
            super().generate(**arguments)

        # Generate content as usual, but reset indent afterwards.
        indent = self.indent
        super().generate(**arguments)
        self.indent = indent

        # Close directive if it is one we previously opened.
        if not hasattr(self, 'directives'):
            return
        if not self.directives:
            return
        (domain, directive, name, markers) = self.directives[-1]
        if domain != getattr(self, 'domain', 'py'):
            return
        if directive != getattr(self, 'directivetype', self.objtype):
            return
        if name != self.format_name():
            return
        self.directives.pop()
        sourcename = self.get_sourcename()
        self.add_line(markers, sourcename)


# Mix the modified Documenter class back in with each directive defined
# by Autodoc, so that they all use the methods overridden above.

class ModuleDocumenter(Documenter, autodoc.ModuleDocumenter):
    pass


class FunctionDocumenter(Documenter, autodoc.FunctionDocumenter):
    pass


class DecoratorDocumenter(Documenter, autodoc.DecoratorDocumenter):
    pass


class ClassDocumenter(Documenter, autodoc.ClassDocumenter):
    pass


class MethodDocumenter(Documenter, autodoc.MethodDocumenter):
    pass


class AttributeDocumenter(Documenter, autodoc.AttributeDocumenter):
    pass


class PropertyDocumenter(Documenter, autodoc.PropertyDocumenter):
    pass


class ExceptionDocumenter(Documenter, autodoc.ExceptionDocumenter):
    pass


class DataDocumenter(Documenter, autodoc.DataDocumenter):
    pass


def setup(app):
    """
    Sets up the extension.

    Sphinx calls this function if the user named this extension in
    `conf.py`. We then set up the Autodoc extension that ships with
    Sphinx and override the generation of domain directives, so that
    the syntax is compatible with the Markdown extension provided by
    MyST instead of the reStructuredText syntax expected by Sphinx.
    """
    app.setup_extension('sphinx.ext.autodoc')
    app.add_autodocumenter(ModuleDocumenter, override=True)
    app.add_autodocumenter(FunctionDocumenter, override=True)
    app.add_autodocumenter(DecoratorDocumenter, override=True)
    app.add_autodocumenter(ClassDocumenter, override=True)
    app.add_autodocumenter(MethodDocumenter, override=True)
    app.add_autodocumenter(AttributeDocumenter, override=True)
    app.add_autodocumenter(PropertyDocumenter, override=True)
    app.add_autodocumenter(ExceptionDocumenter, override=True)
    app.add_autodocumenter(DataDocumenter, override=True)
    return {'version': __version__, 'parallel_read_safe': True}
