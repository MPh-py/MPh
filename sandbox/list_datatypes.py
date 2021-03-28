"""Lists all Java data types used in node properties of the demo model."""

import mph


def list_dtypes():
    for dtype in sorted(dtypes):
        print(f'• {dtype}')


def list_properties(dtype):
    for (group, node, property) in dtypes[dtype]:
        print(f'  {group:10} -> {str(node.name()):20} -> {property}')


client = mph.start()
model = client.load('../tests/capacitor.mph')

groups = {
    'functions':  model.java.func,
    'components': model.java.component,
    'geometries': model.java.geom,
    'selections': model.java.selection,
    'views':      model.java.view,
    'physics':    model.java.physics,
    'materials':  model.java.material,
    'meshes':     model.java.mesh,
    'studies':    model.java.study,
    'solutions':  model.java.sol,
    'plots':      model.java.result,
    'datasets':   model.java.result().dataset,
    'exports':    model.java.result().export,
}

dtypes = {}
for (group, node) in groups.items():
    nodes = [node(tag) for tag in node().tags()]
    for node in nodes:
        if not hasattr(node, 'properties'):
            continue
        for property in node.properties():
            dtype = str(node.getValueType(property))
            if dtype not in dtypes:
                dtypes[dtype] = []
            dtypes[dtype].append((group, node, str(property)))

print(f'Found {len(dtypes)} different data types.')
list_dtypes()
