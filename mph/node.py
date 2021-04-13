"""Provides the wrapper class for a model node."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
from numpy import array, ndarray       # numerical array
from jpype.types import JBoolean       # Java boolean
from jpype.types import JInt           # Java integer
from jpype.types import JDouble        # Java float
from jpype.types import JString        # Java string
from jpype.types import JArray         # Java array
from pathlib import Path               # file-system path
from re import split                   # string splitting
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


########################################
# Node                                #
########################################
class Node:
    """
    Represents a model mode.

    Nodes work similarly to `pathlib.Path` objects from Python's
    standard library. They support string concatenation to the right
    with the `/` operator  in order to reference child nodes:
    ```python
    >>> node = model/'functions'
    >>> node
    Node('functions')
    >>> node/'step'
    Node('functions/step')
    ```

    Note how the `model` object also supports the `/` operator in
    order to generate node references. As mere references, nodes must
    must not necessarily exist in the model tree:
    ```python
    >>> (node/'new function').exists()
    False
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

    This class allows inspecting a node, such as its properties and
    child nodes, as well as manipulating it to some extent, like
    toggling it on/off, creating child nodes, or "running" it. Not all
    actions made available by Comsol are exposed here. Those missing can
    however be triggered in the Java layer, which is accessible via the
    `.java` property.
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, model, path=None):
        if path is None:
            self.path = ('',)
        elif isinstance(path, str):
            self.path = parse(path)
        elif isinstance(path, Node):
            self.path = path.path
        else:
            error = f'Node path {path!r} is not a string or Node instance.'
            logger.error(error)
            raise TypeError(error)
        self.alias = {
            'function':  'functions',
            'component': 'components',
            'geometry':  'geometries',
            'view':      'views',
            'selection': 'selections',
            'variable':  'variables',
            'material':  'materials',
            'mesh':      'meshes',
            'study':     'studies',
            'solution':  'solutions',
            'dataset':   'datasets',
            'plot':      'plots',
            'result':    'plots',
            'results':   'plots',
            'export':    'exports',
        }
        if self.path[0] in self.alias:
            self.path = (self.alias[self.path[0]],) + self.path[1:]
        self.groups = {
            'functions':    model.java.func(),
            'components':   model.java.component(),
            'geometries':   model.java.geom(),
            'views':        model.java.view(),
            'selections':   model.java.selection(),
            'variables':    model.java.variable(),
            'physics':      model.java.physics(),
            'multiphysics': model.java.multiphysics(),
            'materials':    model.java.material(),
            'meshes':       model.java.mesh(),
            'studies':      model.java.study(),
            'solutions':    model.java.sol(),
            'datasets':     model.java.result().dataset(),
            'plots':        model.java.result(),
            'exports':      model.java.result().export(),
        }
        self.model = model

    def __str__(self):
        return join(self.path)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __eq__(self, other):
        return (self.path == other.path and self.model == other.model)

    def __truediv__(self, other):
        if isinstance(other, str):
            other = other.lstrip('/')
            return Node(self.model, join(parse(f'{self}/{other}')))
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
        Returns the Java object this node maps to.

        Note that this is a property, not an attribute. Internally,
        it is a function that performs a top-down search of the model
        tree in order to resolve the node reference. So it introduces
        a certain overhead every time it is accessed.
        """
        if self.is_root():
            return self.model.java
        name = self.name()
        if self.is_group():
            return self.groups.get(name, None)
        parent = self.parent()
        java = parent.java
        if not java:
            return
        container = java if parent.is_group() else java.feature()
        for tag in container.tags():
            member = container.get(tag)
            if name == escape(member.name()):
                return member

    ####################################
    # Navigation                       #
    ####################################

    def name(self):
        """Returns the node's name."""
        return f'{self.model}' if self.is_root() else escape(self.path[-1])

    def tag(self):
        """Returns the node's tag."""
        return str(self.java.tag()) if self.exists() else None

    def type(self):
        """
        Returns the node's feature type.

        This a something like `'Block'` for "a right-angled solid or
        surface block in 3D". Refer to the Comsol documentation for
        details. Feature types are displayed in the Comsol GUI at the
        top of the `Settings` tab.
        """
        return str(self.java.getType())

    def parent(self):
        """Returns the parent node."""
        if self.is_root():
            return None
        else:
            return Node(self.model, join(self.path[:-1]))

    def children(self):
        """Returns all child nodes."""
        java = self.java
        if self.is_root():
            return [Node(self.model, group) for group in self.groups]
        elif self.is_group():
            return [self/escape(java.get(tag).name()) for tag in java.tags()]
        elif hasattr(java, 'feature'):
            return [self/escape(java.feature(tag).name())
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
    # Interaction                      #
    ####################################

    def rename(self, name):
        """Renames the node."""
        if self.is_root():
            error = 'Cannot rename the root node.'
            logger.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot rename a built-in group.'
            logger.error(error)
            raise PermissionError(error)
        self.java.name(name)
        self.path = self.path[:-1] + (name,)

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

    def toggle(self, action='flip'):
        """
        Enables or disables the node.

        If `action` is `'flip'` (the default), it enables the feature
        in the model tree if it is currently disabled or disables it
        if enabled. Pass `'enable'` or `'on'` to enable the feature
        regardless of its current state. Pass `'disable'` or `'off'`
        to disable it.
        """
        if not self.exists():
            error = f'Node {self} does not exist in model tree.'
            logger.error(error)
            raise LookupError(error)
        if action == 'flip':
            self.java.active(not self.java.isActive())
        elif action in ('enable', 'on', 'activate'):
            self.java.active(True)
        elif action in ('disable', 'off', 'deactivate'):
            self.java.active(False)

    def run(self):
        """Performs the "run" action if the node implements it."""
        if not hasattr(self.java, 'run'):
            error = 'Node "{self}" does not implement "run" operation.'
            logger.error(error)
            raise RuntimeError(error)
        self.java.run()

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
            logger.error(error)
            raise PermissionError(error)
        container = self.java if self.is_group() else self.java.feature()
        for argument in arguments:
            if isinstance(argument, str):
                prefix = argument.strip().replace(' ', '_').lower()[:3]
                break
        else:
            prefix = 'tag'
        tag = container.uniquetag(prefix)
        if not arguments:
            container.create(tag)
        else:
            container.create(tag, *[cast(argument) for argument in arguments])
        if name:
            container.get(tag).name(name)
        else:
            name = str(container.get(tag).name())
        return self/name

    def remove(self):
        """Removes the node from the model tree."""
        if self.is_root():
            error = 'Cannot remove the root node.'
            logger.error(error)
            raise PermissionError(error)
        if self.is_group():
            error = 'Cannot remove a built-in group.'
            logger.error(error)
            raise PermissionError(error)
        if not self.exists():
            error = 'Node does not exist in model tree.'
            logger.error(error)
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
    return tuple(unescape(name) for name in split(r'(?<!/)/(?!/)', string))


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
# Type casting                         #
########################################

def cast(value):
    """Casts a value from its Python data type to a suitable Java data type."""
    if isinstance(value, bool):
        return JBoolean(value)
    elif isinstance(value, int):
        return JInt(value)
    elif isinstance(value, float):
        return JDouble(value)
    elif isinstance(value, str):
        return JString(value)
    elif isinstance(value, Path):
        return JString(str(value))
    elif isinstance(value, (list, tuple)):
        dimension = array(value).ndim
        if value == [[]]:
            value = []
        return JArray(JString, dimension)(value)
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
                logger.error(error)
                raise TypeError(error)
            rows = [row.astype(float) for row in value]
            if len(rows) > 2:
                error = 'Will not cast object arrays with more than two rows.'
                logger.error(error)
                raise TypeError(error)
            for row in rows:
                if row.ndim > 1:
                    error = 'Rows in object arrays must be one-dimensional.'
                    logger.error(error)
                    raise TypeError(error)
            return JArray(JDouble, 2)(rows)
        else:
            error = f'Cannot cast arrays of data type "{value.dtype}".'
            logger.error(error)
            raise TypeError(error)
    else:
        error = f'Cannot cast values of data type "{type(value).__name__}".'
        logger.error(error)
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
            logger.error(error)
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
        logger.error(error)
        raise TypeError(error)


########################################
# Inspection                           #
########################################

def inspect(java):
    """
    Inspects a Java node object.

    This is basically a "pretty-fied" version of the output from the
    built-in `dir` command. It displays (prints to the console) the
    methods of a model node (as given by the Comsol API) as well as
    the node's properties (if any are defined).

    The node's name, tag, and documentation reference marker are
    listed first. These access methods and a few others, which are
    common to all objects, are suppressed in the method list further
    down, for the sake of clarity.
    """

    # Display general information about the feature.
    print(f'name:    {java.name()}')
    print(f'tag:     {java.tag()}')
    try:
        print(f'type:    {java.getType()}')
    except AttributeError:
        pass
    print(f'display: {java.getDisplayString()}')
    print(f'doc:     {java.docMarker()}')

    # Display comments and notify if feature is deactivated or has warnings.
    comments = str(java.comments())
    if comments:
        print(f'comment: {comments}')
    if not java.isActive():
        print('This feature is currently deactivated.')
    try:
        if java.hasWarning():
            print('This feature has warnings.')
    except AttributeError:
        pass

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
                'active', 'isActive', 'isactive', 'hasWarning',
                'class_', 'getClass', 'hashCode',
                'notify', 'notifyAll', 'wait']

    # Display the feature's methods.
    print('methods:')
    for name in attributes:
        if name.startswith('_') or name in suppress:
            continue
        print(f'  {name}')


def tree(node, levels=[], max_depth=None):
    """
    Displays the model tree.

    This function displays a representation of the model tree in the
    console. `node` would typically be the model's root node. `levels`
    is used internally when traversing the model tree recursively.
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
