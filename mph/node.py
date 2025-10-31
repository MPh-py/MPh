"""Provides the wrapper class for a model node."""

from __future__ import annotations

from jpype     import JBoolean, JInt, JDouble, JString, JArray, JClass
from numpy     import array, ndarray, integer

from pathlib   import Path
from re        import split
from json      import load as json_load
from difflib   import get_close_matches
from functools import lru_cache
from logging   import getLogger

from typing          import TYPE_CHECKING, overload, Literal, ClassVar
from collections.abc import Iterator, Sequence
from numpy.typing    import ArrayLike, NDArray
from numpy           import int32
if TYPE_CHECKING:
    from .model      import Model


log = getLogger(__package__)


########
# Node #
########

class Node:
    """
    Represents a model node.

    This class makes it possible to navigate the model tree, inspect a node,
    namely its properties, and manipulate it, like toggling it on/off, creating
    child nodes, or "running" it.

    Instances of this class reference a node in the model tree and work
    similarly to [`Path`](#pathlib.Path) objects from Python's standard
    library. They support string concatenation to the right with the division
    operator in order to reference child nodes:
    ```python
    >>> node = model/'functions'
    >>> node
    Node('functions')
    >>> node/'step'
    Node('functions/step')
    ```

    Note how the [`model`](#Model) object also supports the division operator
    in order to generate node references. As mere references, nodes must must
    not necessarily exist in the model tree:
    ```python
    >>> (node/'new function').exists()
    False
    ```

    In interactive sessions, the convenience function [`mph.tree()`](#tree) may
    prove useful to see the node's branch in the model tree at a glance:
    ```console
    >>> mph.tree(model/'physics')
    physics
    ├─ electrostatic
    │  ├─ Laplace equation
    │  ├─ zero charge
    │  ├─ initial values
    │  ├─ anode
    │  └─ cathode
    └─ electric currents
       ├─ current conservation
       ├─ insulation
       ├─ initial values
       ├─ anode
       └─ cathode
    ```

    In rare cases, the node name itself might contain a forward slash, such as
    the dataset `sweep/solution` that happens to exist in the demo model from
    the [Tutorial](/tutorial.md). These literal forward slashes can be escaped
    by doubling the character:
    ```python
    >>> node = model/'datasets/sweep//solution'
    >>> node.name()
    'sweep//solution'
    >>> node.parent()
    Node('datasets')
    ```

    If the node refers to an existing model feature, then the instance wraps
    the corresponding Java object, which could belong to a variety of classes,
    but would necessarily implement the [`com.comsol.model.ModelEntity`][1]
    interface. That Java object can be accessed directly via the `.java`
    property. The full Comsol functionality is thus available if needed. The
    convenience function [`mph.inspect()`](#inspect) is provided for
    introspection of the Java object in an interactive session.

    [1]: https://doc.comsol.com/6.0/doc/com.comsol.help.comsol/api\
/com/comsol/model/ModelEntity.html
    """

    model: Model
    """Model object this node refers to."""

    groups: ClassVar[dict[str, str]] = {
        'parameters':   'self.model.java.param().group()',
        'functions':    'self.model.java.func()',
        'components':   'self.model.java.component()',
        'geometries':   'self.model.java.geom()',
        'views':        'self.model.java.view()',
        'selections':   'self.model.java.selection()',
        'coordinates':  'self.model.java.coordSystem()',
        'variables':    'self.model.java.variable()',
        'couplings':    'self.model.java.cpl()',
        'physics':      'self.model.java.physics()',
        'multiphysics': 'self.model.java.multiphysics()',
        'materials':    'self.model.java.material()',
        'meshes':       'self.model.java.mesh()',
        'studies':      'self.model.java.study()',
        'solutions':    'self.model.java.sol()',
        'batches':      'self.model.java.batch()',
        'datasets':     'self.model.java.result().dataset()',
        'evaluations':  'self.model.java.result().numerical()',
        'tables':       'self.model.java.result().table()',
        'plots':        'self.model.java.result()',
        'exports':      'self.model.java.result().export()',
    }
    """Mapping of the built-in groups to corresponding Java objects."""

    alias: ClassVar[dict[str, str]] = {
        'parameter':  'parameters',
        'function':   'functions',
        'component':  'components',
        'geometry':   'geometries',
        'view':       'views',
        'selection':  'selections',
        'variable':   'variables',
        'coupling':   'couplings',
        'material':   'materials',
        'mesh':       'meshes',
        'study':      'studies',
        'solution':   'solutions',
        'batch':      'batches',
        'dataset':    'datasets',
        'evaluation': 'evaluations',
        'table':      'tables',
        'plot':       'plots',
        'result':     'plots',
        'results':    'plots',
        'export':     'exports',
    }
    """Accepted aliases for the names of built-in groups."""

    path: tuple[str, ...]
    """Path of this node reference from the model's root."""

    ############
    # Internal #
    ############

    def __init__(self, model: Model, node: str | Node = None):
        self.model = model
        if node is None:
            self.path = ('',)
        elif isinstance(node, str):
            parts = parse(node)
            if parts[0] in self.alias:
                parts = (self.alias[parts[0]], *parts[1:])
            self.path = parts
        elif isinstance(node, Node):
            self.path = node.path
        else:
            error = f'Node path {node!r} is not a string or Node instance.'
            log.error(error)
            raise TypeError(error)

    def __str__(self) -> str:
        return join(self.path)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return (self.path == other.path and self.model == other.model)

    def __truediv__(self, other: str) -> Node:
        if isinstance(other, str):
            other = other.lstrip('/')
            return self.__class__(self.model, join(parse(f'{self}/{other}')))
        return NotImplemented

    def __contains__(self, node: str | Node) -> bool:
        if isinstance(node, str) and (self/node).exists():
            return True
        if isinstance(node, Node) and node.parent() == self and node.exists():
            return True
        return False

    def __iter__(self) -> Iterator[Node]:
        yield from self.children()

    @property
    def java(self) -> JClass | None:
        """
        Java object this node maps to, if any.

        Note that this is a property, not an attribute. Internally, it is a
        function that performs a top-down search of the model tree in order to
        resolve the node reference. So it introduces a certain overhead every
        time it is accessed.
        """
        if self.is_root():
            return self.model.java
        name = self.name()
        if self.is_group():
            if name in self.groups:
                return eval(self.groups[name])
            else:
                return None
        parent = self.parent()
        java = parent.java
        if not java:
            return None
        if parent.is_group():
            container = java
        elif hasattr(java, 'propertyGroup'):
            container = java.propertyGroup()
        else:
            container = java.feature()
        for tag in container.tags():
            member = container.get(tag)
            if name == escape(member.label()):
                return member

    def java_if_exists(self) -> JClass:
        # Returns `self.java` if the node exists, raises an error otherwise.
        #
        # This helper function was introduced to reduce code repetition in the
        # methods that follow. We should probably just straight up raise the
        # error when `self.java` is accessed. However, that might break user
        # code, so can only be done in a major release.
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        return java

    ##############
    # Navigation #
    ##############

    def name(self) -> str:
        """Returns the node's name."""
        return f'{self.model}' if self.is_root() else escape(self.path[-1])

    def tag(self) -> str | None:
        """Returns the node's tag."""
        java = self.java
        return str(java.tag()) if java else None

    def type(self) -> str | None:
        """
        Returns the node's feature type.

        This a something like `'Block'` for "a right-angled solid or surface
        block in 3D". Refer to the Comsol documentation for details. Feature
        types are displayed in the Comsol GUI at the top of the `Settings` tab.
        """
        java = self.java
        return str(java.getType()) if hasattr(java, 'getType') else None

    def parent(self) -> Node | None:
        """Returns the parent node."""
        if self.is_root():
            return None
        else:
            return self.__class__(self.model, join(self.path[:-1]))

    def children(self) -> list[Node]:
        """Returns all child nodes."""
        java = self.java
        if self.is_root():
            return [self.__class__(self.model, group) for group in self.groups]
        elif self.is_group():
            return [self/escape(java.get(tag).label()) for tag in java.tags()]
        elif hasattr(java, 'propertyGroup'):
            return [self/escape(java.propertyGroup(tag).label())
                    for tag in java.propertyGroup().tags()]
        elif hasattr(java, 'feature'):
            return [self/escape(java.feature(tag).label())
                    for tag in java.feature().tags()]
        else:
            return []

    def is_root(self) -> bool:
        """Checks if the node is the model's root node."""
        return bool(len(self.path) == 1 and not self.path[0])

    def is_group(self) -> bool:
        """Checks if the node refers to a built-in group."""
        return bool(len(self.path) == 1 and self.path[0])

    def exists(self) -> bool:
        """Checks if the node exists in the model tree."""
        return (self.java is not None)

    ##############
    # Inspection #
    ##############

    def comment(self, text: str = None) -> None | str:
        """Returns or sets the comment attached to the node."""
        java = self.java_if_exists()
        if text is None:
            return str(java.comments())
        else:
            java.comments(text)

    def problems(self) -> list[dict[str, str | Node]]:
        """
        Returns problems reported by the node and its descendants.

        The problems are returned as a list of dictionaries, each with an entry
        for `'message'` (the warning or error message), `'category'` (either
        `'warning'` or `'error'`), `'node'` (either this one or a node beneath
        it in the model tree), and `'selection'` (an empty string if not
        applicable).

        Calling this method on the root node returns all warnings and errors in
        geometry, mesh, and solver sequences.
        """
        java = self.java
        stack = []
        if hasattr(java, 'problem'):
            for tag in java.problem().tags():
                stack.append(java.problem(tag))
        items = []
        while stack:
            problem = stack.pop()
            item = {
                'message':   '',
                'category':  '',
                'node':      self,
                'selection': '',
            }
            if hasattr(problem, 'message'):
                item['message'] = str(problem.message()).strip()
            elif problem.hasProperty('message'):
                item['message'] = str(problem.getString('message')).strip()
            if 'error' in str(problem.getType()).lower():
                item['category'] = 'error'
            elif 'warning' in str(problem.getType()).lower():
                item['category'] = 'warning'
            if hasattr(problem, 'hasSelection') and problem.hasSelection():
                item['selection'] = str(problem.selection())
            items.append(item)
            if hasattr(problem, 'problem'):
                for tag in problem.problem().tags():
                    stack.append(problem.problem(tag))
        for child in self.children():
            items += child.problems()
        return items

    ###############
    # Interaction #
    ###############

    def rename(self, name: str):
        """Renames the node."""
        if self.is_root():
            error = 'Cannot rename the root node.'
            log.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot rename a built-in group.'
            log.error(error)
            raise PermissionError(error)
        java = self.java
        if java:
            java.label(name)
        self.path = (*self.path[:-1], name)

    def retag(self, tag: str):
        """Assigns a new tag to the node."""
        if self.is_root():
            error = 'Cannot change tag of root node.'
            log.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot change tag of built-in group.'
            log.error(error)
            raise PermissionError(error)
        java = self.java_if_exists()
        java.tag(tag)

    @overload
    def property(self,
        name:  str,
        value: bool | float | str | Path | Node | list[Node | str] | ArrayLike,
    ): ...
    @overload
    def property(self,
        name:  str,
        value: None,
    ) -> Node | bool | float | str | Path | NDArray: ...
    def property(self, name, value=None):
        """
        Returns or changes the value of the named property.

        If no `value` is given, returns the value of property `name`. Otherwise
        sets the property to the given value.
        """
        java = self.java_if_exists()
        if value is None:
            return get(java, name)
        else:
            java.set(name, cast(value))

    def properties(self) -> dict[
        str,
        Node | bool | float | str | Path
        | list[str] | list[list[str]] | NDArray
        | None
    ]:
        """
        Returns names and values of all node properties as a dictionary.

        In the Comsol GUI, properties are displayed in the Settings tab of the
        model node (not to be confused with the Properties tab).
        """
        java = self.java_if_exists()
        if not hasattr(java, 'properties'):
            return {}
        names = sorted(str(name) for name in java.properties())
        return {name: get(java, name) for name in names}

    def select(self,
        entity: Literal['all'] | None
                | int | Node
                | Sequence[int] | NDArray[integer],
    ):
        """
        Assigns `entity` as the node's selection.

        `entity` can either be another node representing a selection feature,
        in which case a "named" selection is created. Or it can be a list/array
        of integers denoting domain, boundary, edge, or point numbers
        (depending on which of those the selection requires), producing a
        "manual" selection. It may also be `'all'` to select everything or
        `None` to clear the selection.

        Raises `NotImplementedError` if the node (that this method is called
        on) is a geometry node. Access their Java methods directly. Raises
        `TypeError` if the node does not have a selection and is not itself an
        "explicit" selection.
        """
        java = self.java_if_exists()
        if isinstance(java, JClass('com.comsol.model.GeomFeature')):
            error = "Use the Java layer to change a geometry node's selection."
            log.error(error)
            raise NotImplementedError(error)
        try:
            java = java.selection()
        except Exception:
            if any(not hasattr(java, attr) for attr in ('set', 'all')):
                error = f'Node "{self}" has no and is no (explicit) selection.'
                log.error(error)
                raise TypeError(error) from None
        if isinstance(entity, Node):
            if not hasattr(java, 'named'):
                error = f'Node "{self}" does not support named selections.'
                log.error(error)
                raise TypeError(error)
            node = entity
            if not node.exists():
                error = f'Assigned node "{node}" does not exist.'
                log.error(error)
                raise LookupError(error)
            java.named(node.tag())
        elif isinstance(entity, (list, ndarray)):
            java.set(cast(entity) if len(entity) else None)
        elif isinstance(entity, (int, integer)):
            java.set(cast(entity))
        elif entity == 'all':
            java.all()
        elif entity is None:
            java.set(cast(None))
        else:
            error = "Entity must be a node, 'all', or an array of integers."
            log.error(error)
            raise ValueError(error)

    def selection(self) -> Node | NDArray[int32] | None:
        """
        Returns the entity or entities the node has selected.

        If it is a "named" selection, the corresponding selection node is
        returned. If it is a "manual" selection, an array of domain, boundary,
        edge, or point numbers is returned (depending on which of those the
        selection holds). `None` is returned if nothing is selected.

        Raises `NotImplementedError` if the node is a geometry node. Access
        their Java methods directly. Raises `TypeError` if the node does not
        have a selection and is not itself a selection.
        """
        java = self.java_if_exists()
        if isinstance(java, JClass('com.comsol.model.GeomFeature')):
            error = "Use the Java layer to query a geometry node's selection."
            log.error(error)
            raise NotImplementedError(error)
        try:
            java = java.selection()
        except Exception:
            if not hasattr(java, 'entities'):
                error = f'Node "{self}" has no and is no selection.'
                log.error(error)
                raise TypeError(error) from None
        tag = str(java.named()) if hasattr(java, 'named') else None
        if tag:
            for node in self.model/'selections':
                if tag == node.tag():
                    break
            else:
                error = f'Found no selection with reported tag "{tag}".'
                log.error(error)
                raise LookupError(error)
            return node
        else:
            entities = java.entities()
            return array(entities) if entities else None

    def toggle(self,
        action: Literal[
            'flip',
            'enable', 'disable',
            'on', 'off',
            'activate', 'deactivate',
        ] = 'flip',
    ):
        """
        Enables or disables the node.

        If `action` is `'flip'` (the default), it enables the feature in the
        model tree if it is currently disabled or disables it if enabled. Pass
        `'enable'` or `'on'` to enable the feature regardless of its current
        state. Pass `'disable'` or `'off'` to disable it.
        """
        java = self.java_if_exists()
        if action == 'flip':
            java.active(not java.isActive())
        elif action in ('enable', 'on', 'activate'):
            java.active(True)
        elif action in ('disable', 'off', 'deactivate'):
            java.active(False)

    def run(self):
        """Performs the "run" action if the node implements it."""
        java = self.java_if_exists()
        if not hasattr(java, 'run'):
            error = f'Node "{self}" does not implement "run" operation.'
            log.error(error)
            raise RuntimeError(error)
        java.run()

    def import_(self, file: Path | str):
        """
        Imports external data from the given `file`.

        Note the trailing underscore in the method name. It is needed so that
        the Python parser does not treat the name as an `import` statement.
        """
        file = Path(file)
        if not file.exists():
            error = f'File "{file}" does not exist.'
            log.error(error)
            raise IOError(error)
        log.info(f'Loading external data from file "{file.name}".')
        self.property('filename', f'{file}')
        self.java.discardData()
        self.java.importData()
        log.info('Finished loading external data.')

    def create(self,
        *arguments: Node | bool | float | str | Path | None,
        name:       str = None,
    ):
        """
        Creates a new child feature node.

        Note that this only works for what Comsol considers model "features",
        not for any and all nodes in the model tree (such as property groups of
        materials).

        Refer to the Comsol documentation for valid `arguments`. It is often
        just the feature type of the child node to be created, given as a
        string such as `'Block'`, but may also require different or more
        arguments.

        If `name` is not given, a unique name/label will be assigned
        automatically.

        Returns the node instance of the newly created feature.
        """
        if self.is_root():
            error = 'Cannot create nodes at root of model tree.'
            log.error(error)
            raise PermissionError(error)
        java = self.java
        container = None
        if self.is_group():
            if not hasattr(java, 'uniquetag') and hasattr(java, 'feature'):
                container = java.feature()
            elif hasattr(java, 'uniquetag') and hasattr(java, 'create'):
                container = java
        elif hasattr(java, 'propertyGroup'):
            container = java.propertyGroup()
        elif hasattr(java, 'feature'):
            container = java.feature()
        if not hasattr(container, 'uniquetag'):
            error = f'Node {self} does not support feature creation.'
            log.error(error)
            raise RuntimeError(error)
        for argument in arguments:
            if isinstance(argument, str):
                type = argument
                break
        else:
            type = '?'
        pattern = tag_pattern([*feature_path(self), type])
        if pattern.endswith('*'):
            tag = container.uniquetag(pattern[:-1])
        elif pattern in container.tags():
            tag = container.uniquetag(pattern)
        else:
            tag = pattern
        if not arguments:
            container.create(tag)
        else:
            container.create(tag, *[cast(argument) for argument in arguments])
        if name:
            container.get(tag).label(unescape(name))
        else:
            name = escape(container.get(tag).label())
        child = self/name
        check = tag_pattern(feature_path(child))
        if pattern != check:
            pattern = check
            if pattern.endswith('*'):
                tag = container.uniquetag(pattern[:-1])
            elif pattern in container.tags():
                tag = container.uniquetag(pattern)
            else:
                tag = pattern
            log.debug(f'Retagging "{child}": "{child.tag()}" → "{tag}".')
            child.retag(tag)
        return child

    def remove(self):
        """Removes the node from the model tree."""
        if self.is_root():
            error = 'Cannot remove the root node.'
            log.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot remove a built-in group.'
            log.error(error)
            raise PermissionError(error)
        if not self.exists():
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        parent = self.parent()
        java = parent.java
        if parent.is_group():
            container = java
        elif hasattr(java, 'propertyGroup'):
            container = java.propertyGroup()
        else:
            container = java.feature()
        container.remove(self.java.tag())


################
# Name parsing #
################

def parse(string: str) -> tuple[str, ...]:
    """Parses a node path given as string to a tuple."""
    # Force-cast str subclasses to str, just like `pathlib` does.
    # See bugs.python.org/issue21127 for the rationale.
    string = str(string)
    # Remove all leading and trailing forward slashes.
    string = string.lstrip('/').rstrip('/')
    # Split at forward slashes, but not double forward slashes.
    path = tuple(unescape(name) for name in split(r'(?<!/)/(?!/)', string))
    return path


def join(path: tuple[str, ...]) -> str:
    """Joins a node path given as tuple into a string."""
    return '/'.join(escape(name) for name in path)


def escape(name: str) -> str:
    """Escapes forward slashes in a node name."""
    # Also accept Java strings, but always return Python string.
    name = str(name)
    return name.replace('/', '//')


def unescape(name: str) -> str:
    """Reverses escaping of forward slashes in a node name."""
    return name.replace('//', '/')


################
# Tag patterns #
################

# When creating a new node, we have to assign it a tag. The Comsol API does not
# seem to have a way of suggesting a tag, such as "std1" for the first study.
# That seems to be a feature of Comsol Desktop. Rather than creating generic
# tags such as "tag1", "tag2", etc., we use a heuristic to try and mirror the
# more meaningful tags that the Comsol GUI generates. This is purely cosmetic.
# The tag names don't matter, they just have to be unique.

@lru_cache(maxsize=1)
def load_patterns() -> dict[str, str]:
    """Loads the look-up table for tag patterns indexed by feature path."""
    file = Path(__file__).parent/'tags.json'
    with file.open(encoding='UTF-8-sig') as stream:
        patterns = json_load(stream)
    return patterns


def feature_path(node: Node | None) -> list[str]:
    """Returns the feature path of a node."""
    if node.is_group():
        return [node.name()]
    type = node.type()
    if not type:
        type = '?'
    return [*feature_path(node.parent()), type]


def tag_pattern(feature_path: Sequence[str]):
    """Looks up the tag pattern for the best match to given feature path."""
    (group, type) = (feature_path[0], feature_path[-1])
    patterns = load_patterns()
    selected = [key for key in patterns
                if key.startswith(group) and key.endswith(type)]
    matches = get_close_matches(' → '.join(feature_path), selected)
    if matches:
        return patterns[matches[0]]
    elif type != '?':
        return type.lower()[:3] + '*'
    else:
        return 'tag*'


################
# Type casting #
################

def cast(
    value: None | Node | bool | int | integer | float | str | Path
           | list | tuple | NDArray
) -> JBoolean | JInt | JDouble | JString | JArray | None:
    """Casts a value from its Python data type to a suitable Java data type."""
    if isinstance(value, Node):
        return JString(value.tag())
    elif value is None:
        return value
    elif isinstance(value, bool):
        return JBoolean(value)
    elif isinstance(value, int):
        return JInt(value)
    elif isinstance(value, integer):
        return JInt(int(value))
    elif isinstance(value, float):
        return JDouble(value)
    elif isinstance(value, str):
        return JString(value)
    elif isinstance(value, Path):
        return JString(str(value))
    elif isinstance(value, (list, tuple)):
        dimension = 0
        item = value
        while isinstance(item, (list, tuple)):
            dimension += 1
            if not len(item):
                datatype = JString
                value = []
                break
            item = item[0]
        else:
            datatype = cast(item).__class__
        value = [cast(item) for item in value]
        return JArray(datatype, dimension)(value)
    elif isinstance(value, ndarray):
        if value.dtype.kind == 'b':
            return JArray(JBoolean, value.ndim)(value)
        elif value.dtype.kind == 'f':
            return JArray(JDouble, value.ndim)(value)
        elif value.dtype.kind == 'i':
            return JArray(JInt, value.ndim)(value)
        elif value.dtype.kind == 'O':
            if value.ndim > 2:
                error = 'Cannot cast object arrays of dimension higher than 2.'
                log.error(error)
                raise TypeError(error)
            if len(value) > 2:
                error = 'Will not cast object arrays with more than two rows.'
                log.error(error)
                raise TypeError(error)
            rows = [row.astype(float) for row in value]
            return JArray(JDouble, 2)(rows)
        else:
            error = f'Cannot cast arrays of data type "{value.dtype}".'
            log.error(error)
            raise TypeError(error)
    else:
        error = f'Cannot cast values of data type "{type(value).__name__}".'
        log.error(error)
        raise TypeError(error)


def get(
    java: JClass,
    name: str,
) -> (
    Node
    | bool | float | str | Path
    | list[str] | list[list[str]] | NDArray
    | None
):
    """Returns the value of a Java node property as a Python data type."""
    datatype = java.getValueType(name)
    if datatype == 'Boolean':
        return java.getBoolean(name)
    elif datatype == 'BooleanArray':
        return array(java.getBooleanArray(name))
    elif datatype == 'BooleanMatrix':
        return array([line for line in java.getBooleanMatrix(name)])
    elif datatype == 'Double':
        return java.getDouble(name)
    elif datatype == 'DoubleArray':
        return array(java.getDoubleArray(name))
    elif datatype == 'DoubleMatrix':
        return array([line for line in java.getDoubleMatrix(name)])
    elif datatype == 'DoubleRowMatrix':
        value = java.getDoubleMatrix(name)
        if len(value) == 0:
            rows = []
        elif len(value) == 1:
            rows = [array(value[0])]
        elif len(value) == 2:
            rows = [array(value[0]), array(value[1])]
        else:
            error = 'Cannot convert double-row matrix with more than two rows.'
            log.error(error)
            raise TypeError(error)
        return array(rows, dtype=object)
    elif datatype == 'File':
        return Path(str(java.getString(name)))
    elif datatype == 'Int':
        return int(java.getInt(name))
    elif datatype == 'IntArray':
        return array(java.getIntArray(name))
    elif datatype == 'IntMatrix':
        return array([line for line in java.getIntMatrix(name)])
    elif datatype == 'None':
        return None
    elif datatype == 'Selection':
        return [str(string) for string in java.getEntryKeys(name)]
    elif datatype == 'String':
        value = java.getString(name)
        return str(value) if value else None
    elif datatype == 'StringArray':
        return [str(string) for string in java.getStringArray(name)]
    elif datatype == 'StringMatrix':
        value = java.getStringMatrix(name)
        if value:
            return [[str(string) for string in line] for line in value]
        else:
            return [[]]
    else:
        error = f'Cannot convert Java data type "{datatype}".'
        log.error(error)
        raise TypeError(error)


##############
# Inspection #
##############

def tree(node: Node | Model, max_depth: int = None):
    """
    Displays the model tree.

    This is a convenience function to visualize, in an interactive Python
    session, the branch of the model tree underneath a given [`node`](#Node).
    It produces console output such as this:
    ```console
    >>> mph.tree(model/'physics')
    physics
    ├─ electrostatic
    │  ├─ Laplace equation
    │  ├─ zero charge
    │  ├─ initial values
    │  ├─ anode
    │  └─ cathode
    └─ electric currents
       ├─ current conservation
       ├─ insulation
       ├─ initial values
       ├─ anode
       └─ cathode
    ```

    Specify `max_depth` to possibly limit the number of lower branches.

    Often the node would refer to the model's root in order to inspect the
    entire model tree. A [`Model`](#Model) object is therefore also accepted
    as a value for `node`.

    Note that this function performs poorly in client–server mode, which is the
    default way to communicate with the Comsol backend. The client–server
    communication introduces inefficiencies that do not occur in stand-alone
    mode, where client and backend run in the same process, and the model tree,
    i.e. the hierarchy of related Java objects, can thus be traversed
    reasonably fast.
    """

    def traverse(node: Node, levels: list[bool], max_depth: int | None):
        if max_depth and len(levels) > max_depth:
            return
        markers = ''.join('   ' if last else '│  ' for last in levels[:-1])
        markers += '' if not levels else '└─ ' if levels[-1] else '├─ '
        print(f'{markers}{node.name()}')
        children = node.children()
        last = len(children) - 1
        for (index, child) in enumerate(children):
            traverse(child, [*levels, index == last], max_depth)

    if not isinstance(node, Node):
        # Assume node is actually a model object and traverse from root.
        node = node/None
    traverse(node, [], max_depth)


def inspect(java: JClass | Node | Model):
    """
    Inspects a Java node object.

    This is a convenience function to facilitate exploring Comsol's Java API in
    an interactive Python session. It expects a Java node object, such as the
    one returned by the `.java` property of an existing node reference, which
    would implement the [`com.comsol.model.ModelEntity`][1] interface.

    Like any object, it could also be inspected with Python's built-in `dir`
    command. This function here outputs a "pretty-fied" version of that. It
    displays (prints to the console) the methods implemented by the Java node
    as well as its properties, if any are defined.

    ```console
    >>> mph.inspect((model/'studies').java)
    name:    StudyList
    tag:     study
    display: StudyList
    doc:     StudyList
    methods:
      clear
      copy
      copyTo
      create
      duplicate
      duplicateTo
      equals
      forEach
      get
      getContainer
      index
      iterator
      model
      move
      remove
      scope
      size
      spliterator
      tags
      uniquetag
    ```

    The node's name, tag, and documentation reference marker are listed first.
    These access methods and a few others, which are common to all objects, are
    suppressed in the method list further down, for the sake of clarity.

    [1]: https://doc.comsol.com/6.0/doc/com.comsol.help.comsol/api\
/com/comsol/model/ModelEntity.html
    """

    # Also accept Node and Model instances.
    if hasattr(java, 'java'):
        java = java.java

    # Display general information about the feature.
    print(f'name:    {java.label()}')
    print(f'tag:     {java.tag()}')
    if hasattr(java, 'getType'):
        print(f'type:    {java.getType()}')
    print(f'display: {java.getDisplayString()}')
    print(f'doc:     {java.docMarker()}')

    # Display comments and notify if feature is deactivated or has warnings.
    comments = str(java.comments())
    if comments:
        print(f'comment: {comments}')
    if not java.isActive():
        print('This feature is currently deactivated.')

    # Introspect the feature's attributes.
    attributes = [attribute for attribute in dir(java)]

    # Display properties if any are defined.
    if 'properties' in attributes:
        print('properties:')
        names = [str(name) for name in java.properties()]
        for name in names:
            try:
                value = get(java, name)
            except Exception as error:
                value = f'<{error}>'
            print(f'  {name}: {value}')

    # Define a list of common methods to be suppressed in the output.
    suppress = ['name', 'label', 'tag', 'getType', 'getDisplayString',
                'docMarker', 'help', 'comments', 'toString', 'icon',
                'properties', 'hasProperty', 'set',
                'getEntryKeys', 'getEntryKeyIndex', 'getValueType',
                'getInt',     'getIntArray',     'getIntMatrix',
                'getBoolean', 'getBooleanArray', 'getBooleanMatrix',
                'getDouble',  'getDoubleArray',  'getDoubleMatrix',
                'getString',  'getStringArray',  'getStringMatrix',
                'version', 'author', 'resetAuthor', 'lastModifiedBy',
                'dateCreated', 'dateModified', 'timeCreated', 'timeModified',
                'active', 'isActive', 'isactive',
                'class_', 'getClass', 'hashCode',
                'notify', 'notifyAll', 'wait']

    # Display the feature's methods.
    print('methods:')
    for name in attributes:
        if name.startswith('_') or name in suppress:
            continue
        print(f'  {name}')
