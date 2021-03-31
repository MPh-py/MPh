"""
Demonstrates feature creation anywhere in the model tree.

The functions starting with "java_" return Java objects and are
intended to be moved to the `java` module.
"""
import mph
import logging
logging.basicConfig(level=20)

# Start Comsol session.
client = mph.start()
model = client.create('my model')

# Java-like syntax for comparison:
# model.modelNode().create("comp1");
# model.geom().create("geom1", 3);
# model.geom("geom1").feature().create("blk1", "Block");
# model.geom("geom1").feature("blk1").set("size", ["0.1", "0.2", "0.5"]);
# model.geom("geom1").run("fin");

# Create features using pythonic syntax.
component = model.create('components')
geometry = model.create('geometries', 3)
block = model.create(geometry / 'big block', 'Block', auto_name=False)
model.property(block, 'size', ('0.1', '0.2', '0.5'))
model.build(geometry.name())

print('geometry:', geometry.java)
print(20*'-')
print('block:', block.java)
print(20*'-')
print('block parent (not geometry):', block.parent().java)
print(20*'-')
print('block container:', block.java.getContainer())
print(20*'-')
print('Parent inspection does not have remove: ')
mph.inspect(block.parent().java)
print(20*'-')
print('Container inspection has remove: ')
mph.inspect(block.java.getContainer())

# Test removing nodes.
# model.remove(block)
# model.remove(geometry)
# model.remove(component)
