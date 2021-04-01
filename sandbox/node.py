"""Provides the wrapper class for a model node."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from mph import java                   # Java layer


########################################
# Dependencies                         #
########################################
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
    Represents a node in the model tree.
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, model, path='/'):
        if isinstance(path, str):
            self.path = tuple(str(path).lstrip('/').rstrip('/').split('/'))
        elif isinstance(path, Node):
            self.path = path.path
        else:
            error = f'Node path {path!r} is not a string or Node object.'
            logger.error(error)
            raise TypeError(error)
        self.model = model
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
        if not self.is_root() and self.path[0] in self.alias:
            self.path = (self.alias[self.path[0]],) + self.path[1:]
        self.groups = {
            'functions':    self.model.java.func(),
            'components':   self.model.java.component(),
            'geometries':   self.model.java.geom(),
            'views':        self.model.java.view(),
            'selections':   self.model.java.selection(),
            'variables':    self.model.java.variable(),
            'physics':      self.model.java.physics(),
            'multiphysics': self.model.java.multiphysics(),
            'materials':    self.model.java.material(),
            'meshes':       self.model.java.mesh(),
            'studies':      self.model.java.study(),
            'solutions':    self.model.java.sol(),
            'plots':        self.model.java.result(),
            'datasets':     self.model.java.result().dataset(),
            'exports':      self.model.java.result().export(),
        }

    def __eq__(self, other):
        return (self.path == other.path and self.model == other.model)

    def __str__(self):
        return '/' + '/'.join(self.path)

    def __repr__(self):
        return f'{self.__class__.__name__}([{self.model.name()}]{self})'

    def __truediv__(self, other):
        if isinstance(other, str):
            return Node(self.model, str(self) + '/' + str(other).lstrip('/'))
        else:
            return NotImplemented

    @property
    def java(self):
        """Returns the corresponding Java object for the node."""
        if self.is_root():
            return self.model.java
        name = self.name()
        if self.is_group():
            if name in self.groups:
                return self.groups[name]
            else:
                error = f'No top-level group named "{name}".'
                logger.error(error)
                raise LookupError(error)
        parent = self.parent()
        if parent.is_group():
            container = parent.java
        else:
            container = parent.java.feature()
        for tag in container.tags():
            member = container.get(tag)
            if name == str(member.name()):
                return member
        else:
            error = f'Node "{self}" does not exist.'
            logger.error(error)
            raise LookupError(error)

    ####################################
    # Navigation                       #
    ####################################

    def name(self):
        """Returns the node's name."""
        if self.is_root():
            return '/'
        else:
            return self.path[-1]

    def exists(self):
        """Checks if the node exists in the model."""
        try:
            self.java
            return True
        except LookupError:
            return False

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
            tags  = [tag for tag in self.java.tags()]
            names = [str(self.java.get(tag).name()) for tag in tags]
            paths = [self.path + (name,) for name in names]
            nodes = [Node(self.model, '/'.join(path)) for path in paths]
            return nodes
        else:
            if not hasattr(self.java, 'feature'):
                return []
            tags  = [tag for tag in self.java.feature().tags()]
            names = [str(self.java.feature(tag).name()) for tag in tags]
            paths = [self.path + (name,) for name in names]
            nodes = [Node(self.model, '/'.join(path)) for path in paths]
            return nodes

    def is_root(self):
        """Checks if node is the model's root."""
        return bool(len(self.path) == 1 and not self.path[0])

    def is_group(self):
        """Checks if node is a top-level group."""
        return bool(len(self.path) == 1 and self.path[0])

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
        return java.property(self.java, name, value)

    def create(self, *arguments, name=None):
        """
        Creates a new child node.

        Refer to the Comsol documentation for the values of valid
        arguments. It is often just the type of the child node to be
        created, but may include other options.

        If `name` is not given, a unique name/label will automatically
        be assigned.
        """
        if self.is_root():
            error = 'Cannot create nodes at root of model tree.'
            logger.error(error)
            raise PermissionError(error)
        if self.is_group():
            container = self.java
        else:
            container = self.java.feature()
        # To do: Diversify tag names. Use feature type if possible.
        tag = container.uniquetag('tag')
        if not arguments:
            container.create(tag)
        else:
            # To do: Arguments should be type-cast from Python to Java.
            container.create(tag, *arguments)
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
        if self.parent().is_group():
            container = self.parent().java
        else:
            container = self.parent().java.feature()
        container.remove(self.java.tag())
