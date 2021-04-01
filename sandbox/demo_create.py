"""
Demonstrates feature creation anywhere in the model tree.

The functions starting with "java_" return Java objects and are
intended to be moved to the `java` module.
"""

import mph
from mph import java


def java_groups(model):
    """Returns the top-level groups as Java objects."""
    return {
        'function':     model.java.func(),
        'component':    model.java.component(),
        'geometry':     model.java.geom(),
        'view':         model.java.view(),
        'selection':    model.java.selection(),
        'variable':     model.java.variable(),
        'physics':      model.java.physics(),
        'multiphysics': model.java.multiphysics(),
        'material':     model.java.material(),
        'mesh':         model.java.mesh(),
        'study':        model.java.study(),
        'solution':     model.java.sol(),
        'plot':         model.java.result(),
        'dataset':      model.java.result().dataset(),
        'export':       model.java.result().export(),
    }


def java_node(model, path):
    """Returns the model node at the given path as a Java object."""
    if not isinstance(path, tuple):
        error = f'Node path must be a tuple of strings, not "{path}".'
        raise TypeError(error)
    (*parent, child) = path
    parent = tuple(parent)
    if not isinstance(child, str):
        error = f'Node path component "{child}" is not a string.'
        raise TypeError(error)
    if not parent:
        return java_groups(model)[child]
    group = java_node(model, parent)
    if hasattr(group, 'feature'):
        group = group.feature()
    if not hasattr(group, 'tags'):
        error = f'Node {parent} is not a group node.'
        raise ValueError(error)
    tags = [tag for tag in group.tags()]
    names = [group.get(tag).name() for tag in tags]
    if child not in names:
        error = f'No node named "{child}" in group {parent}.'
        raise LookupError(error)
    tag = tags[names.index(child)]
    return group.get(tag)


def normalize(path):
    """Returns the normalized node path after possible concatenation."""
    def flatten(path):
        if isinstance(path, (tuple, list)):
            for part in path:
                yield from flatten(part)
        else:
            yield path
    return tuple(flatten(path))


class NewModel(mph.Model):
    """Modified model wrapper."""

    def create(self, node, *arguments):
        node = normalize(node)
        try:
            group = java_node(self, node)
            parent = node
            child  = None
        except LookupError:
            (*parent, child) = node
            parent = tuple(parent)
            group = java_node(self, parent)
        if hasattr(group, 'feature'):
            group = group.feature()
        # To do: Diversify tag names. Use feature type if possible.
        tag = group.uniquetag('tag')
        if not arguments:
            group.create(tag)
        else:
            # To do: Arguments should be type-cast from Python to Java.
            group.create(tag, *arguments)
        if child:
            group.get(tag).name(child)
        else:
            child = str(group.get(tag).name())
        return normalize( (parent, child) )

    def property(self, node, name, value=None):
        feature = java_node(self, normalize(node))
        java.property(feature, name, value)

    def remove(self, node):
        feature = java_node(self, normalize(node))
        parent = feature.getContainer()
        parent.remove(feature.tag())

    def build(self, geometry=None):
        if isinstance(geometry, str):
            super().build(geometry)
        else:
            super().build(geometry[-1])


# Start Comsol session.
client = mph.start()
model = NewModel(client.create('my model'))

# Java-like syntax for comparison:
# model.modelNode().create("comp1");
# model.geom().create("geom1", 3);
# model.geom("geom1").feature().create("blk1", "Block");
# model.geom("geom1").feature("blk1").set("size", ["0.1", "0.2", "0.5"]);
# model.geom("geom1").run("fin");

# Create features using pythonic syntax.
component = model.create('component')
geometry = model.create('geometry', 3)
block = model.create((geometry, 'big block'), 'Block')
model.property(block, 'size', ('0.1', '0.2', '0.5'))
model.build(geometry)

# Test removing nodes.
model.remove(block)
model.remove(geometry)
model.remove(component)
