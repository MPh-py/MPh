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
    Refers to a node in the model tree.

    Nodes work similarly to `pathlib.Path` objects from Python's
    standard library. They support string concatenation to the right
    with the `/` operator  in order to reference child nodes:
    ```python
    >>> node = model/'functions'
    >>> node
    Node('/functions')
    >>> node/'step'
    Node('/functions/step')
    ```

    Note how the `model` object also supports the `/` operator in
    order to generate node references. As mere references, nodes must
    must not necessarily exist in the model tree:
    ```python
    >>> (node/'new function').exists()
    False
    ```

    This class allows inspecting a node, such as its properties and
    child nodes, as well as manipulating it to some extent, like
    toggling it on/off, creating child nodes, or "running" it. Not all
    actions made available by Comsol are exposed through this class.
    Those missing could be triggered from the Java layer, which is
    accessible via the `.java` property.
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, model, path='/'):
        if isinstance(path, str):
            # Force-cast str subclasses to str, just like `pathlib` does.
            # See bugs.python.org/issue21127 for the rationale.
            self.path = tuple(str(path).lstrip('/').rstrip('/').split('/'))
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
            'plot':      'plots',
            'result':    'plots',
            'results':   'plots',
            'dataset':   'datasets',
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
            'plots':        model.java.result(),
            'datasets':     model.java.result().dataset(),
            'exports':      model.java.result().export(),
        }
        self.model = model

    def __str__(self):
        return '/' + '/'.join(self.path)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __eq__(self, other):
        return (self.path == other.path and self.model == other.model)

    def __truediv__(self, other):
        if isinstance(other, str):
            return Node(self.model, str(self) + '/' + str(other).lstrip('/'))
        else:
            return NotImplemented

    @property
    def java(self):
        """Returns the Java object this node maps to."""
        if self.is_root():
            return self.model.java
        name = self.name()
        if self.is_group():
            return self.groups.get(name, None)
        parent = self.parent()
        container = parent.java if parent.is_group() else parent.java.feature()
        for tag in container.tags():
            member = container.get(tag)
            if name == str(member.name()):
                return member

    ####################################
    # Navigation                       #
    ####################################

    def name(self):
        """Returns the node's name."""
        return '/' if self.is_root() else self.path[-1]

    def tag(self):
        """Returns the node's tag."""
        return str(self.java.tag()) if self.exists() else None

    def parent(self):
        """Returns the parent node."""
        if self.is_root():
            return None
        else:
            return Node(self.model, '/'.join(self.path[:-1]))

    def children(self):
        """Returns all child nodes."""
        if self.is_root():
            return [Node(self.model, group) for group in self.groups]
        elif self.is_group():
            return [self/str(self.java.get(tag).name())
                    for tag in self.java.tags()]
        elif hasattr(self.java, 'feature'):
            return [self/str(self.java.feature(tag).name())
                    for tag in self.java.feature().tags()]
        else:
            return []

    def is_root(self):
        """Checks if node is the model's root."""
        return bool(len(self.path) == 1 and not self.path[0])

    def is_group(self):
        """Checks if the node refers to a built-in top-level group."""
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
            error = 'Cannot rename a top-level group.'
            logger.error(error)
            raise PermissionError(error)
        self.java.name(name)
        self.path = self.path[:-1] + (name,)

    def properties(self):
        """Returns the names of all node properties."""
        return [str(name) for name in self.java.properties()]

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
        arguments. It is often just the feature type of the child node
        to be created, given as a string such as `'Block'`, but may
        also require different or more arguments.

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
            error = 'Cannot remove a top-level group.'
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
# Type-casting                         #
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
        return value
    elif isinstance(value, ndarray):
        if value.dtype in (int, float, bool):
            return JArray.of(value)
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
    elif datatype == 'String':
        return str(java.getString(name))
    elif datatype == 'StringArray':
        return [str(string) for string in java.getStringArray(name)]
    elif datatype == 'StringMatrix':
        return [[str(string) for string in line]
                for line in java.getStringMatrix(name)]
    else:
        raise TypeError(f'Cannot convert Java data type "{datatype}".')


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
        names = [str(property) for property in java.properties()]
        for name in names:
            try:
                value = get(java, name)
            except TypeError:
                value = '[?]'
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
