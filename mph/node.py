"""Provides the wrapper for Comsol model objects."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
from logging import getLogger          # event logging

########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


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

    def createJava(self, *arguments):
        if self.exists():
            logger.info('Node already exists in model tree')
            return self.java

        else:
            if self._rootnode:
                logger.error('Cannot create root nodes')
                return None

            root, path, name = self._path[0], self._path[1:-1], self._path[-1]

            if path:
                # traverse into the tree
                group = self._node(root, path[0])
                for path_level in path[1:]:
                    group = _subnode(group, path_level)
                group = group.feature()

            else:
                group = self._model._group(root)

            # To do: Diversify tag names. Use feature type if possible.
            tag = group.uniquetag('tag')
            if not arguments:
                group.create(tag)
            else:
                # To do: Arguments should be type-cast from Python to Java.
                group.create(tag, *arguments)

            if name != 'none':
                group.get(tag).label(name)
            else:
                name = str(group.get(tag).name())
                self._path = self._path[:-1] + (name,)

            self.java = self._traverse()

    def _node(self, group, name):
        # Returns the named model node inside a given group.
        parent = self._model._group(group)
        tags = [tag for tag in parent.tags()]
        names = [str(parent.get(tag).name()) for tag in tags]
        try:
            node = parent.get(tags[names.index(name)])
        except ValueError:
            error = f'No node named "{name}" in group "{group}".'
            logger.debug(error)
            raise LookupError(error) from None
        return node

    def _traverse(self):
        """
        Retuns a node java specified via the path member.
        """
        if self._rootnode:
            return self._model._group(self._path[0])

        root, path, name = self._path[0], self._path[1:-1], self._path[-1]

        if path:
            # traverse into the tree
            level = self._node(root, path[0])
            for path_level in path[1:]:
                level = _subnode(level, path_level)
            node = _subnode(level, name)

        else:
            # get the root node and return
            node = self._node(root, name)

        return node

    def is_root(self):
        return self._rootnode

    def path(self):
        return self.__str__()

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
