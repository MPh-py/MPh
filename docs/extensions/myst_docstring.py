"""
MyST-compatible drop-in replacement for Sphinx's Autodoc extension

This extension overrides Autodoc's generation of [domain] directives
so that the syntax is what the MyST Markdown parser expects, instead of
Sphinx's own reStructuredText parser.

Note that this is very much a hack, and that we simply assume that all
doc-strings are written in MyST-flavored Markdown. However, unless your
mileage differs, this here does make all of Sphinx's features available
in Markdown, e.g. cross-references to other parts of the documentation.

© 2022–2023 John Hennig, [MIT license]

[domain]: https://www.sphinx-doc.org/en/master/usage/restructuredtext\
/domains.html
[MIT license]: https://www.tldrlegal.com/license/mit-license
"""
__version__ = '0.3.0'


from sphinx.ext import autodoc


class Documenter(autodoc.Documenter):
    """
    Mix-in to override content generation by `Documenter` class.

    All of Autodoc's documenter classes (for modules, functions, etc.)
    derive from the `Documenter` base class. Three of its methods are
    important:
    * The one that adds the directive header, i.e. opens the directive.
    * The one that generates the content, which includes the actual
      doc-string as well as documentation for all child elements, such
      as methods of a class.
    * The one methods that adds lines of generated mark-up.

    We assume that all doc-strings are written in Markdown. All we
    need to do then is convert the reStructuredText that Autodoc
    generates to MyST-flavored Markdown. There isn't much syntax
    complexity to worry about (or so we presume), so we'll just search
    and replace the syntax of domain directives that Autodoc adds.

    A complication, however, is that in reStructuredText the scope of
    directives is designated by indentation, whereas in Markdown
    directives are delimited by enclosing fences (triple back-ticks).
    These would typically be nested by adding extra back-ticks at each
    nesting level, for example four back-ticks for the outer directive
    when a directive delimited with the regular three back-ticks is
    nested inside.

    To make our life easier, we use a little known feature of MyST, or
    perhaps Markdown-it: We may also nest directives delimited by
    exactly three back-ticks, ` ``` `, inside directives delimited by
    three tildes, `~~~`. Then indentation *is* significant, and we
    don't have to keep track of additional back-ticks. Though we
    still need to close the directive's scope.

    Ideally, Autodoc would be aware of such structural syntax
    requirements. But it's not. And it doesn't call out to the parser
    anyway, it simply generates reStructuredText no matter what. A
    robust solution would either make Autodoc parser-aware or, better,
    not have it generate intermediate mark-up at all and instead
    produce Docutils nodes like Sphinx extensions should actually do.
    """

    def add_directive_header(self, sig):
        """Adds the directive header and options."""

        # Remembered we opened this directive.
        # We add our own "stack" of directives to keep track of them.
        if not hasattr(self, 'directives'):
            self.directives = []
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        self.directives.append( (domain, directive, name) )

        # Let super method render directive header in reStructuredText.
        # It will call `add_line()` repeatedly, which we intercept there
        # to convert to Markdown after the fact.
        super().add_directive_header(sig)

        # Close directive immediately if it is a module.
        # Module directives are a special case in that way.
        if (domain, directive) == ('py', 'module'):
            self.directives.pop()
            self.add_line('~~~', self.get_sourcename())

    def generate(self, **arguments):
        """Generates documentation for the object and its members."""

        # Let super method render directive body.
        super().generate(**arguments)

        # Close the directive if it's the one we last opened.
        if not hasattr(self, 'directives') or not self.directives:
            return
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name = self.format_name()
        (domain_, directive_, name_) = self.directives[-1]
        if (domain_, directive_, name_) != (domain, directive, name):
            return
        self.directives.pop()
        self.indent = self.indent.removeprefix('   ')
        prefix = '```' if self.indent else '~~~'
        self.add_line(prefix, self.get_sourcename())

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        """Append one line of generated mark-up to the output."""

        # Pass through empty lines.
        if not line.strip():
            self.directive.result.append('', source, *lineno)
            return

        # Convert syntax of domain directives at start of line.
        domain = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        prefix = f'.. {domain}:{directive}::'
        if line.startswith(prefix):
            line = line.removeprefix(prefix)
            if self.indent:
                prefix = '```{' + f'{domain}:{directive}' + '}'
            else:
                prefix = '~~~{' + f'{domain}:{directive}' + '}'
            line = prefix + line
        self.directive.result.append(self.indent + line, source, *lineno)


# Mix the modified Documenter class back in with each directive defined
# by Autodoc, so that they all inherit the methods overridden above.

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
    Sphinx and override the generation of domain directives.
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
