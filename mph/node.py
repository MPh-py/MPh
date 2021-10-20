"""Provides the wrapper class for a model node."""

########################################
# Dependencies                         #
########################################
from numpy import array, ndarray       # numerical array
from jpype import JBoolean             # Java boolean
from jpype import JInt                 # Java integer
from jpype import JDouble              # Java float
from jpype import JString              # Java string
from jpype import JArray               # Java array
from jpype import JClass               # Java class
from numpy import integer              # NumPy integer
from pathlib import Path               # file-system path
from re import split                   # string splitting
from json import load as json_load     # JSON decoder
from difflib import get_close_matches  # fuzzy matching
from functools import lru_cache        # function cache
from logging import getLogger          # event logging

########################################
# Globals                              #
########################################
log = getLogger(__package__)           # event log


########################################
# Node                                #
########################################
class Node:
    """
    Represents a model node.

    This class makes it possible to navigate the model tree, inspect a
    node, namely its properties, and manipulate it, like toggling it
    on/off, creating child nodes, or "running" it.

    Instances of this class reference a node in the model tree and work
    similarly to `pathlib.Path` objects from Python's standard library.
    They support string concatenation to the right with the division
    operator in order to reference child nodes:
    ```python
    >>> node = model/'functions'
    >>> node
    Node('functions')
    >>> node/'step'
    Node('functions/step')
    ```

    Note how the `model` object also supports the division operator in
    order to generate node references. As mere references, nodes must
    must not necessarily exist in the model tree:
    ```python
    >>> (node/'new function').exists()
    False
    ```

    In interactive sessions, the convenience function `mph.tree()` may
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

    In rare cases, the node name itself might contain a forward slash,
    such as the dataset `sweep/solution` that happens to exist in the
    demo model from the Tutorial. These literal forward slashes can be
    escaped by doubling the character:
    ```python
    >>> node = model/'datasets/sweep//solution'
    >>> node.name()
    'sweep//solution'
    >>> node.parent()
    Node('datasets')
    ```

    If the node refers to an existing model feature, then the instance
    wraps the corresponding Java object, which could belong to a variety
    of classes, but would necessarily implement the
    [com.comsol.model.ModelEntity][1] interface. That Java object
    can be accessed directly via the `.java` property. The full Comsol
    functionality is thus available if needed. The convenience function
    `mph.inspect()` is provided for introspection of the Java object in
    an interactive session.

    [1]: https://doc.comsol.com/5.6/doc/com.comsol.help.comsol/api\
/com/comsol/model/ModelEntity.html
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, model, path=None):
        if path is None:
            path = ('',)
        elif isinstance(path, str):
            path = parse(path)
        elif isinstance(path, Node):
            path = path.path
        else:
            error = f'Node path {path!r} is not a string or Node instance.'
            log.error(error)
            raise TypeError(error)
        self.model = model
        """Model object this node refers to."""
        self.groups = {
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
        self.alias = {
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
        if path[0] in self.alias:
            path = (self.alias[path[0]],) + path[1:]
        self.path = path
        """Path of this node reference from the model's root."""

    def __str__(self):
        return join(self.path)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __eq__(self, other):
        return (self.path == other.path and self.model == other.model)

    def __truediv__(self, other):
        if isinstance(other, str):
            other = other.lstrip('/')
            return self.__class__(self.model, join(parse(f'{self}/{other}')))
        return NotImplemented

    def __contains__(self, node):
        if isinstance(node, str):
            if (self/node).exists():
                return True
        elif isinstance(node, Node):
            if node.parent() == self and node.exists():
                return True
        return False

    def __iter__(self):
        yield from self.children()

    @property
    def java(self):
        """
        Java object this node maps to, if any.

        Note that this is a property, not an attribute. Internally,
        it is a function that performs a top-down search of the model
        tree in order to resolve the node reference. So it introduces
        a certain overhead every time it is accessed.
        """
        if self.is_root():
            return self.model.java
        name = self.name()
        if self.is_group():
            return eval(self.groups.get(name))
        parent = self.parent()
        java = parent.java
        if not java:
            return None
        container = java if parent.is_group() else java.feature()
        for tag in container.tags():
            member = container.get(tag)
            if name == escape(member.label()):
                return member

    ####################################
    # Navigation                       #
    ####################################

    def name(self):
        """Returns the node's name."""
        return f'{self.model}' if self.is_root() else escape(self.path[-1])

    def tag(self):
        """Returns the node's tag."""
        java = self.java
        return str(java.tag()) if java else None

    def type(self):
        """
        Returns the node's feature type.

        This a something like `'Block'` for "a right-angled solid or
        surface block in 3D". Refer to the Comsol documentation for
        details. Feature types are displayed in the Comsol GUI at the
        top of the `Settings` tab.
        """
        java = self.java
        return str(java.getType()) if hasattr(java, 'getType') else None

    def parent(self):
        """Returns the parent node."""
        if self.is_root():
            return None
        else:
            return self.__class__(self.model, join(self.path[:-1]))

    def children(self):
        """Returns all child nodes."""
        java = self.java
        if self.is_root():
            return [self.__class__(self.model, group) for group in self.groups]
        elif self.is_group():
            return [self/escape(java.get(tag).label()) for tag in java.tags()]
        elif hasattr(java, 'feature'):
            return [self/escape(java.feature(tag).label())
                    for tag in java.feature().tags()]
        else:
            return []

    def is_root(self):
        """Checks if the node is the model's root node."""
        return bool(len(self.path) == 1 and not self.path[0])

    def is_group(self):
        """Checks if the node refers to a built-in group."""
        return bool(len(self.path) == 1 and self.path[0])

    def exists(self):
        """Checks if the node exists in the model tree."""
        return (self.java is not None)

    ####################################
    # Inspection                       #
    ####################################

    def comment(self, text=None):
        """Returns or sets the comment attached to the node."""
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        if text is None:
            return str(java.comments())
        else:
            java.comments(text)

    def problems(self):
        """
        Returns problems reported by the node and its descendants.

        The problems are returned as a list of dictionaries, each with
        an entry for `'message'` (the warning or error message),
        `'category'` (either `'warning'` or `'error'`), `'node'` (either
        this one or a node beneath it in the model tree), and
        `'selection'` (an empty string if not applicable).

        Calling this method on the root node returns all warnings and
        errors in geometry, mesh, and solver sequences.
        """
        java = self.java
        stack = []
        if hasattr(java, 'problem'):
            for tag in java.problem().tags():
                stack.append( (self, java, java.problem(tag)) )
        items = []
        while stack:
            (node, parent, problem) = stack.pop()
            item = {
                'message':   '',
                'category':  '',
                'node':      node,
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
            else:
                item['selection'] = ''
            items.append(item)
            if hasattr(problem, 'problem'):
                for tag in problem.problem().tags():
                    stack.append( (node, problem, problem.problem(tag)) )
        for child in self.children():
            items += child.problems()
        return items

    ####################################
    # Interaction                      #
    ####################################

    def rename(self, name):
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
        self.path = self.path[:-1] + (name,)

    def retag(self, tag):
        """Assigns a new tag to the node."""
        if self.is_root():
            error = 'Cannot change tag of root node.'
            log.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot change tag of built-in group.'
            log.error(error)
            raise PermissionError(error)
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        java.tag(tag)

    def property(self, name, value=None):
        """
        Returns or changes the value of the named property.

        If no `value` is given, returns the value of property `name`.
        Otherwise sets the property to the given value.
        """
        if value is None:
            return get(self.java, name)
        else:
            self.java.set(name, cast(value))

    def properties(self):
        """Returns names and values of all node properties as a dictionary."""
        java = self.java
        if not hasattr(java, 'properties'):
            return {}
        names = sorted(str(name) for name in java.properties())
        return {name: get(java, name) for name in names}

    def select(self, entity):
        """
        Assigns `entity` as the node's selection.

        `entity` can either be another node representing a selection
        feature, in which case a "named" selection is created. Or it
        can be a list/array of integers denoting domain, boundary,
        edge, or point numbers (depending on which of those the selection
        requires), producing a "manual" selection. It may also be `'all'`
        to select everything or `None` to clear the selection.

        Raises `NotImplementedError` if the node (that this method is
        called on) is a geometry node. These may be supported in a
        future release. Meanwhile, access their Java methods directly.
        Raises `TypeError` if the node does not have a selection and
        is not itself an "explicit" selection.
        """
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
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

    def selection(self):
        """
        Returns the entity or entities the node has selected.

        If it is a "named" selection, the corresponding selection node
        is returned. If it is a "manual" selection, an array of domain,
        boundary, edge, or point numbers is returned (depending on
        which of those the selection holds). `None` is returned if
        nothing is selected.

        Raises `NotImplementedError` if the node is a geometry node.
        These may be supported in a future release. Meanwhile, access
        their Java methods directly. Raises `TypeError` if the node
        does not have a selection and is not itself a selection.
        """
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
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

    def toggle(self, action='flip'):
        """
        Enables or disables the node.

        If `action` is `'flip'` (the default), it enables the feature
        in the model tree if it is currently disabled or disables it
        if enabled. Pass `'enable'` or `'on'` to enable the feature
        regardless of its current state. Pass `'disable'` or `'off'`
        to disable it.
        """
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        if action == 'flip':
            java.active(not java.isActive())
        elif action in ('enable', 'on', 'activate'):
            java.active(True)
        elif action in ('disable', 'off', 'deactivate'):
            java.active(False)

    def run(self):
        """Performs the "run" action if the node implements it."""
        java = self.java
        if not java:
            error = f'Node "{self}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        if not hasattr(java, 'run'):
            error = f'Node "{self}" does not implement "run" operation.'
            log.error(error)
            raise RuntimeError(error)
        java.run()

    def import_(self, file):
        """
        Imports external data from the given `file`.

        Note the trailing underscore in the method name. It is needed
        so that the Python parser does not treat the name as an
        `import` statement.
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

    def create(self, *arguments, name=None):
        """
        Creates a new child node.

        Refer to the Comsol documentation for the values of valid
        `arguments`. It is often just the feature type of the child
        node to be created, given as a string such as `'Block'`, but
        may also require different or more arguments.

        If `name` is not given, a unique name/label will be assigned
        automatically.
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
        pattern = tag_pattern(feature_path(self) + [type])
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
        container = parent.java if parent.is_group() else parent.java.feature()
        container.remove(self.java.tag())


########################################
# Name parsing                         #
########################################

def parse(string):
    """Parses a node path given as string to a tuple."""
    # Force-cast str subclasses to str, just like `pathlib` does.
    # See bugs.python.org/issue21127 for the rationale.
    string = str(string)
    # Remove all leading and trailing forward slashes.
    string = string.lstrip('/').rstrip('/')
    # Split at forward slashes, but not double forward slashes.
    path = tuple(unescape(name) for name in split(r'(?<!/)/(?!/)', string))
    return path


def join(path):
    """Joins a node path given as tuple into a string."""
    return '/'.join(escape(name) for name in path)


def escape(name):
    """Escapes forward slashes in a node name."""
    # Also accept Java strings, but always return Python string.
    name = str(name)
    return name.replace('/', '//')


def unescape(name):
    """Reverses escaping of forward slashes in a node name."""
    return name.replace('//', '/')


########################################
# Tag patterns                         #
########################################

@lru_cache(maxsize=1)
def load_patterns():
    """Loads the look-up table for tag patterns indexed by feature path."""
    file = Path(__file__).parent/'tags.json'
    with file.open(encoding='UTF-8-sig') as stream:
        patterns = json_load(stream)
    return patterns


def feature_path(node):
    """Returns the feature path of a node."""
    if node.is_group():
        return [node.name()]
    type = node.type()
    if not type:
        type = '?'
    return feature_path(node.parent()) + [type]


def tag_pattern(feature_path):
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


########################################
# Type casting                         #
########################################

def cast(value):
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


def get(java, name):
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


########################################
# Inspection                           #
########################################

def tree(node, levels=[], max_depth=None):
    """
    Displays the model tree.

    This is a convenience function to visualize, in an interactive
    Python session, the branch of the model tree underneath a given
    `node`. It produces console output such as this:
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

    Often the node would refer to the model's root in order to inspect
    the entire model tree. The model object itself is therefore also
    accepted as an argument.

    `levels` is used internally when traversing the model tree recursively.
    Specify `max_depth` to possibly limit the number of lower branches.

    Note that this function performs poorly in client–server mode, the
    default on Linux and macOS, especially for complex models. The
    client–server communication introduces inefficiencies that do not
    occur in stand-alone mode, the default on Windows, where the model
    tree, i.e. the hierarchy of related Java objects, can be traversed
    reasonably fast.
    """
    if not isinstance(node, Node):
        # Support passing the model directly instead of a node.
        node = node/None
    if max_depth and len(levels) > max_depth:
        return
    markers = ''.join('   ' if last else '│  ' for last in levels[:-1])
    markers += '' if not levels else '└─ ' if levels[-1] else '├─ '
    print(f'{markers}{node.name()}')
    children = node.children()
    last = len(children) - 1
    for (index, child) in enumerate(children):
        tree(child, levels + [index == last], max_depth)


def inspect(java):
    """
    Inspects a Java node object.

    This is a convenience function to facilitate exploring Comsol's
    Java API in an interactive Python session. It expects a Java
    node object, such as the one returned by the `.java` property
    of an existing node reference, which would implement the
    [com.comsol.model.ModelEntity][1] interface.

    Like any object, it could also be inspected with Python's built-in
    `dir` command. This function here outputs a "pretty-fied" version
    of that. It displays (prints to the console) the methods implemented
    by the Java node as well as its properties, if any are defined.

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

    The node's name, tag, and documentation reference marker are
    listed first. These access methods and a few others, which are
    common to all objects, are suppressed in the method list further
    down, for the sake of clarity.

    [1]: https://doc.comsol.com/5.6/doc/com.comsol.help.comsol/api\
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
            value = get(java, name)
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
