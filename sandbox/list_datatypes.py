"""Lists Java data types used in node properties of the demo model."""

import mph


def search_tree(node):
    java = node.java
    names = list(java.properties()) if hasattr(java, 'properties') else []
    for name in names:
        datatype = str(java.getValueType(name))
        if datatype not in datatypes:
            datatypes[datatype] = []
        datatypes[datatype].append((node, name))
    for child in node:
        search_tree(child)


def list_datatypes():
    for datatype in sorted(datatypes):
        print(f'• {datatype}')


def list_properties(datatype):
    for (node, name) in datatypes[datatype]:
        print(f'{node} → {name}')


client = mph.start()
model = client.load('../tests/capacitor.mph')

datatypes = {}
search_tree(model/None)

print(f'Found {len(datatypes)} different data types.')
list_datatypes()
