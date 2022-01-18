"""MyST-compatible drop-in replacement for Sphinx's Autodoc extension."""
__version__ = '0.1.0'

# This extension essentially overrides all content creation done by
# Autodoc so that the output is Markdown to be parsed by MyST, instead
# of the original reStructuredText parsed by Sphinx directly. It is
# therefore prone to breakage when there are upstream changes.
#
# Namely, the overridden methods are `add_line`, `add_directive_header`,
# and `generate` of Autodoc's `Documenter` class, as well as of all
# classes derived from it, implementing the various directives for
# modules, functions, etc. Code comments here only pertain to changes
# made to the original code for reST, the original comments from the
# Autodoc source were removed so as to not be a distraction. Type hints
# were also removed, but could easily be put back in. String interpolation
# was changed to f-strings. We use our own logger name, but could have
# kept using Autodoc's. Some variable names were shortened, like `source`
# instead of `sourcename`, to keep lines under 80 characters.


import sphinx
from sphinx.ext import autodoc
from sphinx.util import inspect
from sphinx.pycode import ModuleAnalyzer, PycodeError
from sphinx.ext.autodoc.mock import ismock
from sphinx.util.typing import get_type_hints, stringify, restify
import re

logger = sphinx.util.logging.getLogger(__name__)


class Documenter(autodoc.Documenter):
    """
    Mix-in to override content generation by `Documenter` class.

    All of Autodoc's documenter classes (for modules, functions, etc.)
    derive from the `Documenter` base. Methods that generate reST will
    have to be rewritten to output Markdown instead. They are defined
    here to be mixed into the the various documenter classes.
    """

    def fence(self):
        """
        Returns back-ticks fence corresponding to indentation level.

        The indentation level in the reST output corresponds to the scope
        of the directive block in Markdown, which is delimited by back-ticks.
        The further out the scope, the more back-ticks we have to put. This
        helper function returns a string with the correct number of ticks
        based on the indentation level in the original reStructuredText.
        The indentation level is determined by the current indentation and
        the length of indentation that would be used to nest content.
        """
        unit = self.content_indent or '   '
        (scope, remainder) = divmod(len(self.indent), len(unit))
        if remainder:
            raise RuntimeError(f'Indentation not a multiple of {len(unit)}.')
        if scope > 1:
            raise NotImplementedError('More than one nested scope in Autodoc '
                                      'directive.')
        backticks = '```' + '`'*(2 - scope)
        return backticks

    def add_line(self, line, source, *lineno):
        """Appends one line to the generated output."""
        # Add content, but without the original indentation.
        self.directive.result.append(line, source, *lineno)

    def add_directive_header(self, signature):
        """Adds directive header and options to the generated content."""
        domain    = getattr(self, 'domain', 'py')
        directive = getattr(self, 'directivetype', self.objtype)
        name      = self.format_name()
        source    = self.get_sourcename()
        prefix    = self.fence() + '{' + f'{domain}:{directive}' + '} '
        # This code dealing with multi-line signature was rewritten, for
        # brevity, but is entirely untested.
        (first, *rest) = signature.split('\n')
        self.add_line(f'{prefix}{name}{first}', source)
        for line in rest:
            indent = ' '*len(prefix)
            self.add_line(f'{indent}{name}{first}', source)
        # Add field-list options, but drop the original indentation.
        if self.options.noindex:
            self.add_line(':noindex:', source)
        if self.objpath:
            self.add_line(f':module: {self.modname}', source)

    def generate(self, more_content=None, real_modname=None,
                       check_module=False, all_members=False):
        """
        Generates the Markdown content replacing an Autodoc directive.

        We don't call the corresponding method from the parent class,
        but rather rewrite it with Markdown output. This is done to
        avoid parsing the generated reStructuredText, which is possible,
        but might be error-prone.
        """

        # Until noted otherwise, code is the same as in the parent class.
        # See source code comments there for clarification.

        if not self.parse_name():
            # Have parent class log the corresponding warning.
            super().generate(more_content, real_modname, check_module,
                             all_members)
            return

        if not self.import_object():
            return

        guess_modname = self.get_real_modname()
        self.real_modname: str = real_modname or guess_modname

        try:
            self.analyzer = ModuleAnalyzer.for_module(self.real_modname)
            self.analyzer.find_attr_docs()
        except PycodeError as exc:
            logger.debug(f'[myst-docstring] module analyzer failed: {exc}')
            self.analyzer = None
            if hasattr(self.module, '__file__') and self.module.__file__:
                self.directive.record_dependencies.add(self.module.__file__)
        else:
            self.directive.record_dependencies.add(self.analyzer.srcname)

        if self.real_modname != guess_modname:
            try:
                analyzer = ModuleAnalyzer.for_module(guess_modname)
                self.directive.record_dependencies.add(analyzer.srcname)
            except PycodeError:
                pass

        docstrings = sum(self.get_doc() or [], [])
        if ismock(self.object) and not docstrings:
            logger.warning(
                sphinx.locale.__(f'A mocked object is detected: {self.name}'),
                type='myst-docstring')
        if check_module:
            if not self.check_module():
                return

        source = self.get_sourcename()
        self.add_line('', source)
        try:
            signature = self.format_signature()
        except Exception as exc:
            logger.warning(
                sphinx.locale.__('Error while formatting signature for '
                                 f'{self.fullname}: {exc}'),
                type='myst-docstring')
            return

        # From here on, we make changes to accommodate the Markdown syntax.

        # Generate the directive header and options.
        self.add_directive_header(signature)
        self.add_line('', source)

        # Some directives don't have body content, namely modules. Then
        # there is nothing to indent in reST and the `content_indent`
        # attribute of the corresponding Autodoc class will be an empty
        # string. In Markdown, we have to close these directives right
        # after the signature. The actual content, think members of a
        # module, still follows, but is not syntactically part of the
        # directive block.
        fence = self.fence()
        if not self.content_indent:
            self.add_line(fence, source)

        # Document this object and its members.
        save_indent = self.indent
        self.indent += self.content_indent
        self.add_content(more_content)
        self.document_members(all_members)
        self.indent = save_indent

        # Close directive block, unless closed previously.
        if self.content_indent:
            self.add_line(fence, source)


def mystify(cls):
    """Convert Python class to a MyST reference."""
    # This helper function is entirely untested.
    return re.sub(r':py:(\w+?):`(.+?)`', r'{py:\1}`\2`', restify(cls))


# Mix the modified Documenter class back in with each directive defined
# by Autodoc, so that they all use the methods overridden above. Unless
# these classes override the same methods themselves, in which case we
# have to redefine them as well, since super() would otherwise resolve
# them incorrectly. (It may be possible to override the method resolution
# order by means of a meta class, but that's a lot of black magic.)

class ModuleDocumenter(Documenter, autodoc.ModuleDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        super().add_directive_header(signature)
        source = self.get_sourcename()
        if self.options.synopsis:
            self.add_line(f':synopsis: {self.options.synopsis}', source)
        if self.options.platform:
            self.add_line(f':platform: {self.options.platform}', source)
        if self.options.deprecated:
            self.add_line(':deprecated:', source)


class FunctionDocumenter(Documenter, autodoc.FunctionDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        source = self.get_sourcename()
        super().add_directive_header(signature)
        if (inspect.iscoroutinefunction(self.object)
              or inspect.isasyncgenfunction(self.object)):
            self.add_line(':async:', source)


class DecoratorDocumenter(Documenter, autodoc.DecoratorDocumenter):
    pass


class ClassDocumenter(Documenter, autodoc.ClassDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        source = self.get_sourcename()
        if self.doc_as_attr:
            self.directivetype = 'attribute'
        super().add_directive_header(signature)
        if self.analyzer and '.'.join(self.objpath) in self.analyzer.finals:
            self.add_line(':final:', source)
        canonical_fullname = self.get_canonical_fullname()
        if (not self.doc_as_attr
              and canonical_fullname
              and self.fullname != canonical_fullname):
            self.add_line(f':canonical: {canonical_fullname}', source)
        if not self.doc_as_attr and self.options.show_inheritance:
            if inspect.getorigbases(self.object):
                bases = list(self.object.__orig_bases__)
            elif (hasattr(self.object, '__bases__')
                    and len(self.object.__bases__)):
                bases = list(self.object.__bases__)
            else:
                bases = []
            self.env.events.emit('autodoc-process-bases', self.fullname,
                                 self.object, self.options, bases)
            # Replaced `restify` with `mystify`.
            base_classes = [mystify(cls) for cls in bases]
            source = self.get_sourcename()
            self.add_line('', source)
            self.add_line(
                sphinx.locale._(f'Bases: {", ".join(base_classes)}'),
                source)

    def generate(self, more_content=None, real_modname=None,
                       check_module=False, all_members=False):
        # Unchanged. See original source-code comment for clarification.
        return super().generate(more_content=more_content,
                                check_module=check_module,
                                all_members=all_members)


class MethodDocumenter(Documenter, autodoc.MethodDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        super().add_directive_header(signature)
        source = self.get_sourcename()
        obj = self.parent.__dict__.get(self.object_name, self.object)
        if inspect.isabstractmethod(obj):
            self.add_line(':abstractmethod:', source)
        if inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj):
            self.add_line(':async:', source)
        if inspect.isclassmethod(obj):
            self.add_line(':classmethod:', source)
        if inspect.isstaticmethod(obj, cls=self.parent, name=self.object_name):
            self.add_line(':staticmethod:', source)
        if self.analyzer and '.'.join(self.objpath) in self.analyzer.finals:
            self.add_line(':final:', source)


class AttributeDocumenter(Documenter, autodoc.AttributeDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        super().add_directive_header(signature)
        source = self.get_sourcename()
        if (self.options.annotation is autodoc.SUPPRESS
              or self.should_suppress_directive_header()):
            pass
        elif self.options.annotation:
            self.add_line(f':annotation: {self.options.annotation}', source)
        else:
            if self.config.autodoc_typehints != 'none':
                annotations = get_type_hints(self.parent, None,
                                             self.config.autodoc_type_aliases)
                if self.objpath[-1] in annotations:
                    objrepr = stringify(annotations.get(self.objpath[-1]))
                    self.add_line(f':type: {objrepr}', source)
            try:
                if (self.options.no_value
                      or self.should_suppress_value_header()
                      or ismock(self.object)):
                    pass
                else:
                    objrepr = inspect.object_description(self.object)
                    self.add_line(f':value: {objrepr}', source)
            except ValueError:
                pass


class NewTypeAttributeDocumenter(Documenter,
                                 autodoc.NewTypeAttributeDocumenter):
    pass


class PropertyDocumenter(Documenter, autodoc.PropertyDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        super().add_directive_header(signature)
        source = self.get_sourcename()
        if inspect.isabstractmethod(self.object):
            self.add_line(':abstractmethod:', source)
        if self.isclassmethod:
            self.add_line(':classmethod:', source)
        if inspect.safe_getattr(self.object, 'fget', None):
            func = self.object.fget
        elif inspect.safe_getattr(self.object, 'func', None):
            func = self.object.func
        else:
            func = None
        if func and self.config.autodoc_typehints != 'none':
            try:
                signature = inspect.signature(func,
                                type_aliases=self.config.autodoc_type_aliases)
                if signature.return_annotation is not inspect.Parameter.empty:
                    objrepr = stringify(signature.return_annotation)
                    self.add_line(f':type: {objrepr}', source)
            except TypeError as exc:
                logger.warning(
                    sphinx.locale.__('Failed to get a function signature for '
                                     f'{self.fullname}:{exc}'),
                    type='myst-docstring')
                return None
            except ValueError:
                return None


class ExceptionDocumenter(Documenter, autodoc.ExceptionDocumenter):
    pass


class DataDocumenter(Documenter, autodoc.DataDocumenter):

    def add_directive_header(self, signature):
        # Add field-list options, but drop the original indentation.
        super().add_directive_header(signature)
        source = self.get_sourcename()
        if (self.options.annotation is autodoc.SUPPRESS
              or self.should_suppress_directive_header()):
            pass
        elif self.options.annotation:
            self.add_line(f':annotation: {self.options.annotation}', source)
        else:
            if self.config.autodoc_typehints != 'none':
                annotations = get_type_hints(self.parent, None,
                                             self.config.autodoc_type_aliases)
                if self.objpath[-1] in annotations:
                    objrepr = stringify(annotations.get(self.objpath[-1]))
                    self.add_line(f':type: {objrepr}', source)
            try:
                if (self.options.no_value
                      or self.should_suppress_value_header()
                      or ismock(self.object)):
                    pass
                else:
                    objrepr = inspect.object_description(self.object)
                    # Added quotation marks to avoid errors with values
                    # that happen to contain curly braces. This does not
                    # seem to be necessary in reST, but apparently is
                    # in Markdown.
                    self.add_line(f':value: "{objrepr}"', source)
            except ValueError:
                pass


class NewTypeDataDocumenter(Documenter, autodoc.NewTypeDataDocumenter):
    pass


def setup(app):
    """
    Sets up the extension.

    Sphinx calls this function if the user named the extension in `conf.py`.
    It then sets up the Autodoc extension that ships with Sphinx and
    overrides whatever necessary to produce Markdown to be parsed by MyST
    instead of reStructuredText parsed by Sphinx/Docutils.
    """
    app.setup_extension('sphinx.ext.autodoc')
    app.add_autodocumenter(ModuleDocumenter, override=True)
    app.add_autodocumenter(FunctionDocumenter, override=True)
    app.add_autodocumenter(DecoratorDocumenter, override=True)
    app.add_autodocumenter(ClassDocumenter, override=True)
    app.add_autodocumenter(MethodDocumenter, override=True)
    app.add_autodocumenter(AttributeDocumenter, override=True)
    app.add_autodocumenter(NewTypeAttributeDocumenter, override=True)
    app.add_autodocumenter(PropertyDocumenter, override=True)
    app.add_autodocumenter(ExceptionDocumenter, override=True)
    app.add_autodocumenter(DataDocumenter, override=True)
    app.add_autodocumenter(NewTypeDataDocumenter, override=True)
    return {'version': __version__, 'parallel_read_safe': True}
