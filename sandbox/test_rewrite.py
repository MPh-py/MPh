"""
Tests reading and writing back all node properties in the demo model.

This test is already part of the test suite, but is replicated here
in case something fails. The script can then be run with
`python -i test_rewrite.py` to drop onto the interactive prompt and
figure out when went wrong with the last property.

The script displays a count of how many properties have been tested
successfully. There are a little over 4200 properties total defined
in the demo model.

The test runs much faster in stand-alone mode, the default on Windows,
where it completes in about 10 seconds. In client-server mode, the
default on Linux and macOS, it takes much longer, like 10 *minutes*
and up. This points to some inefficiency in the implementation of
client-server communication and serialization (passing objects back
and forth), something that MPh has no control over.
"""

import mph
from numpy import array
from jpype import JArray, JDouble

# Override default session mode for the purpose of this test.
mph.option('session', 'stand-alone')

# Start session and load demo model.
print('Starting session.')
client = mph.start()
print('Loading model.')
model = client.load('../tests/capacitor.mph')

# Track last node and property name if recursive test fails somewhere.
last_node = None
last_name = None

# Count how many node properties we have successfully tested.
count = 0


# Use recursion to test on every level of the model tree.
def test_rewrite(node):
    global last_node, last_name, count
    last_node = node
    java = node.java
    if hasattr(java, 'properties'):
        names = [str(name) for name in java.properties()]
    else:
        names = []
    for name in names:
        last_name = name
        value = node.property(name)
        if java.getValueType(name) == 'Selection':
            # Changing selections is not (yet) implemented.
            continue
        if name == 'sol' and node.parent().name() == 'parametric solutions':
            # Writing "sol" changes certain node names.
            continue
        node.property(name, value)
        count += 1
        print(count)
    for child in node:
        test_rewrite(child)


# Python values that have caused issues in the past when casting to Java.
p0 = array([[]], dtype=object)
p1 = array([[1,2,3]], dtype=object)
p2 = array([[1,2,3],[4,5]], dtype=object)

# The corresponding Java types that the Python values should map to.
j0 = JArray(JDouble, 2)([[]])
j1 = JArray(JDouble, 2)([[1,2,3]])
j2 = JArray(JDouble, 2)([[1,2,3], [4,5]])

# Example of an empty double-row matrix.
node0 = model/'studies/static/Stationary'
name0 = 'plistarr'

# Example of a double-row matrix where the second row is empty.
node1 = model/'studies/sweep/Parametric Sweep'
name1 = 'plistarr'

# Example of a double-row matrix that is a "ragged" array.
node2 = model/'solutions/time-dependent solution/variables'
name2 = 'clist'

# Run test now to then debug on interactive prompt if any conversion fails.
print('Running test.')
test_rewrite(model/None)
