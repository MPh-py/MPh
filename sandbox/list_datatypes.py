"""Lists Java data types used in node properties of the demo model."""

import mph


def list_datatypes():
    for datatype in sorted(datatypes):
        print(f'• {datatype}')


def list_properties(datatype):
    for (group, node, property) in datatypes[datatype]:
        print(f'  {group:10} -> {str(node.name()):20} -> {property}')


client = mph.start()
model = client.load('../tests/capacitor.mph')

groups = {
    'functions':    model.java.func,
    'components':   model.java.component,
    'geometries':   model.java.geom,
    'views':        model.java.view,
    'selections':   model.java.selection,
    'variables':    model.java.variable,
    'physics':      model.java.physics,
    'multiphysics': model.java.multiphysics,
    'materials':    model.java.material,
    'meshes':       model.java.mesh,
    'studies':      model.java.study,
    'solutions':    model.java.sol,
    'plots':        model.java.result,
    'datasets':     model.java.result().dataset,
    'exports':      model.java.result().export,
}

datatypes = {}
for (group, node) in groups.items():
    nodes = [node(tag) for tag in node().tags()]
    for node in nodes:
        if not hasattr(node, 'properties'):
            continue
        for property in node.properties():
            datatype = str(node.getValueType(property))
            if datatype not in datatypes:
                datatypes[datatype] = []
            datatypes[datatype].append((group, node, str(property)))

print(f'Found {len(datatypes)} different data types.')
list_datatypes()
