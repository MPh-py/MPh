"""Tests the implementation of the prototype for the `Node` class."""

import mph
from node import Node

client = mph.start()
model = client.load('../tests/capacitor.mph')

node = Node(model, '/functions')
print(f'name:     {node.name()}')
print(f'string    {node}')
print(f'repr:     {node!r}')
print(f'root:     {node.is_root()}')
print(f'group:    {node.is_group()}')
print(f'parent:   {node.parent()}')
children = ', '.join(f'{child.name()}' for child in node.children())
print(f'children: {children}')
print(f'exists:   {node.exists()}')
print()

node1 = Node(model, '/function')
node2 = Node(model, '/functions')
assert node1 == node2

mesh = Node(model, '/meshes/mesh')
triangular = mesh.create('FreeTri', name='triangular')
(mesh/'Size').rename('default size')
size = triangular.create('Size', name='size')
size.property('custom', 'on')
size.property('hmax', '1[mm]')
size.property('hmaxactive', True)
size.property('hmin', '0.1[mm]')
size.property('hminactive', False)
size.property('hgrad', 1.5)
size.property('hgradactive', True)
model.mesh(mesh.name())
size.remove()
triangular.remove()

new = client.create('new')
geometries = Node(new, '/geometries')
geometry = geometries.create(3)
block = geometry.create('Block', name='big block')
block.property('size', ('0.1', '0.2', '0.5'))
new.build(geometry.name())


def walk(node, levels=[]):
    markers = ''.join('   ' if last else '│  ' for last in levels[:-1])
    markers += '' if not levels else '└─ ' if levels[-1] else '├─ '
    print(f'{markers}{node.name()}')
    children = node.children()
    last = len(children) - 1
    for (index, child) in enumerate(children):
        walk(child, levels + [index == last])


root = Node(model)
walk(root)
