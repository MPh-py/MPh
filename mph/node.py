"""Provides the wrapper for Comsol model objects."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
from logging import getLogger          # event logging
from pathlib import Path

########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


def _node(parent, name):
    # Returns the named model node inside a given group.
    tags = [tag for tag in parent.tags()]
    names = [str(parent.get(tag).name()) for tag in tags]
    try:
        node = parent.get(tags[names.index(name)])
    except ValueError:
        error = f'No node named "{name}" in group "{parent.name()}".'
        logger.debug(error)
        raise LookupError(error) from None
    return node

def _subnode(level, name):
    # Returns a node from a subgroup
    tags = [tag for tag in level.feature().tags()]
    names = [str(level.feature(tag).name()) for tag in tags]
    try:
        subnode = level.feature(tags[names.index(name)])
    except ValueError:
        error = f'No node named "{name}" in level "{level}".'
        logger.debug(error)
        raise LookupError(error) from None
    return subnode


########################################
# Node                                #
########################################

class Node:
    """
    Nodes should be generated by the model. If generated solo, you need to
    supply the model instance!
    """
    def __init__(self, model, path):
        if isinstance(path, str):
            self._path = tuple(path.split('/'))
        else:
            error = 'Invalid notation'
            logger.error(error)
            raise RuntimeError(error)

        # Check if the path was detected
        if not self._path:
            error = 'Initialization error'
            logger.error(error)
            raise RuntimeError(error)

        # Node arguments as defined by COMSOL - this is needed for
        # graceful delete
        self.comsol_arguments = None

        # Model reference
        self._model = model

        # Check if this is root, if so check if ok
        if len(self._path) == 1:
            self._rootnode = True
            if self._path[0] not in self._model._groups:
                error = 'Root node does not exist'
                logger.error(error)
                raise RuntimeError(error)
        else:
            self._rootnode = False

        # Node location is ok. Does it exist as java?
        if self.exists():
            self.java = self._traverse()
        else:
            self.java = None

    def __str__(self):
        return '/'.join(self._path)

    def __repr__(self):
        exist_string = 'exists' if self.exists() else 'does not exist'
        return f'Node instance at {self.__str__()}, java {exist_string} ({hex(id(self))})'

    def __truediv__(self, other):
        """Returns absolute pathes from concatenation, as pathlib.Path does"""
        if not isinstance(other, (Node, str)):
            raise ValueError('Invalid concatenation types')

        # To facilitate th rather complex truediv, we tread nodes as what they
        # are: pathes.
        path_1 = '/' + '/'.join(self.path())
        if isinstance(other, Node):
            if self._model != other._model:
                raise ValueError('Node concatenation can only be performed with '
                                 'nodes in the same model.')
            path_2 = Path('/' + '/'.join(other.path()))
        elif isinstance(other, str):
            path_2 = Path(other)

        concat = str(Path(path_1) / path_2)[1:]

        return Node(self._model, concat)

    def _traverse(self):
        """
        Retuns a node java specified via the path member.
        """
        if self._rootnode:
            return self._model._group(self._path[0])

        root, path, name = self._path[0], self._path[1:-1], self._path[-1]

        if path:
            # traverse into the tree
            level = _node(self._model._group(root), path[0])
            for path_level in path[1:]:
                level = _subnode(level, path_level)
            node = _subnode(level, name)

        else:
            # get the root node and return
            node = _node(self._model._group(root), name)

        return node

    def _rename(self, name):
        if self.exists():
            self.java.label(str(name))
        self._path = self._path[:-1] + (name,)

    def name(self):
        return self._path[-1]

    def path_elements(self):
        return self._path[0], self._path[1:-1], self._path[-1]

    def is_root(self):
        return self._rootnode

    def path(self):
        return self._path

    def exists(self):
        # Test down to the node if this is (still) a valid one
        if self._rootnode:
            return self._path[0] in self._model._groups
        else:
            try:
                _ = self._traverse()
                return True
            except LookupError:
                return False

    def parent(self):
        # returns the parent node level which is implicitly defined by
        # getContainer(). Not useful for root nodes, raise warning there
        if self.exists():
            if self._rootnode:
                logger.debug('Root parent would be model which is useless here')
                return self.java
            else:
                return self.java.getContainer()

        # If the node does not exist a traverse into the tree is needed stopping
        # one level above
        else:
            root, path = self._path[0], self._path[1:-1]

            if path:
                # traverse into the tree
                level = _node(self._model._group(root), path[0])
                for path_level in path[1:]:
                    level = _subnode(level, path_level)
                return level

            else:
                # get the root node and return
                return self._model._group(root)

    def update_java(self):
        try:
            self.java = self._traverse()
        except LookupError:
            logger.warning('Cannot update java since node does not exist.')
