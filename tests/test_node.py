"""Tests the Node class."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from mph import node, Node
from numpy import array, isclose
from sys import argv
from pathlib import Path
import logging


########################################
# Fixtures                             #
########################################
client = None
model  = None


def setup_module():
    global client, model
    client = mph.start()
    here = Path(__file__).parent
    model = client.load(here/'capacitor.mph')


def teardown_module():
    pass


########################################
# Tests                                #
########################################

def test_parse():
    assert node.parse('a/b')        == ('a', 'b')
    assert node.parse('/a/b')       == ('a', 'b')
    assert node.parse('a/b/')       == ('a', 'b')
    assert node.parse('/a/b/')      == ('a', 'b')
    assert node.parse('a/b/c')      == ('a', 'b', 'c')
    assert node.parse('a/b//c')     == ('a', 'b/c')
    assert node.parse('a//b/c')     == ('a/b', 'c')
    assert node.parse('//a//b/c//') == ('a/b', 'c')
    assert node.parse('a//b/c//d')  == ('a/b', 'c/d')


def test_join():
    assert node.join(('a', 'b'))      == 'a/b'
    assert node.join(('a', 'b', 'c')) == 'a/b/c'
    assert node.join(('a', 'b/c'))    == 'a/b//c'
    assert node.join(('a/b', 'c'))    == 'a//b/c'
    assert node.join(('a/b', 'c/d'))  == 'a//b/c//d'


def test_escape():
    assert node.escape('a/b')   == 'a//b'
    assert node.escape('a//b')  == 'a////b'
    assert node.escape('a/b/c') == 'a//b//c'


def test_unescape():
    assert node.unescape('a//b')    == 'a/b'
    assert node.unescape('a////b')  == 'a//b'
    assert node.unescape('a//b//c') == 'a/b/c'


def test_init():
    node = Node(model, 'functions')
    assert node.model
    assert node.alias
    assert node.groups


def test_str():
    assert str(Node(model, 'functions/step')) == 'functions/step'


def test_repr():
    assert repr(Node(model, 'functions/step')) == "Node('functions/step')"


def test_eq():
    assert Node(model, 'function/step') == Node(model, '/functions/step/')


def test_truediv():
    assert Node(model, 'functions')/'step' == Node(model, 'functions/step')


def test_contains():
    assert 'step' in Node(model, 'functions')
    assert 'other' not in Node(model, 'functions')
    assert Node(model, 'functions/step') in Node(model, 'functions')
    assert Node(model, 'functions/other') not in Node(model, 'functions')


def test_iter():
    assert Node(model, 'functions/step')  in list(Node(model, 'functions'))
    assert Node(model, 'functions/image') in list(Node(model, 'functions'))


def test_java():
    assert Node(model, 'functions').java
    assert Node(model, 'functions/step').java


def test_name():
    assert Node(model, 'functions').name() == 'functions'
    assert Node(model, 'functions/step').name() == 'step'


def test_tag():
    assert Node(model, 'functions/step').tag() == 'step1'


def test_type():
    assert Node(model, 'functions/step').type() == 'Step'
    assert Node(model, 'functions/image').type() == 'Image'
    assert Node(model, 'functions/table').type() == 'Interpolation'


def test_parent():
    assert Node(model, 'functions/step').parent() == Node(model, 'functions')


def test_children():
    assert Node(model, 'functions/step') in Node(model, 'functions').children()
    datasets = Node(model, 'datasets').children()
    assert Node(model, 'datasets/sweep//solution') in datasets
    assert Node(model, 'datasets/sweep//solution').exists()
    assert not Node(model, 'datasets/sweep/solution').exists()


def test_is_root():
    assert Node(model, None).is_root()
    assert Node(model, '').is_root()
    assert Node(model, '/').is_root()


def test_is_group():
    assert Node(model, 'functions').is_group()


def test_exists():
    assert Node(model, 'functions').exists()
    assert Node(model, 'functions/step').exists()
    assert not Node(model, 'functions/new').exists()


def test_rename():
    node = Node(model, 'functions/step')
    name = node.name()
    renamed = Node(model, 'functions/renamed')
    assert not renamed.exists()
    node.rename('renamed')
    assert node.exists()
    assert renamed.exists()
    node.rename(name)
    assert node.exists()
    assert not renamed.exists()


def test_rewrite(node):
    java = node.java
    if hasattr(java, 'properties'):
        names = [str(name) for name in java.properties()]
    else:
        names = []
    for name in names:
        value = node.property(name)
        if java.getValueType(name) == 'Selection':
            # Changing selections is not (yet) implemented.
            continue
        if name == 'sol' and node.parent().name() == 'parametric solutions':
            # Writing "sol" changes certain node names.
            continue
        node.property(name, value)
    for child in node:
        test_rewrite(child)


def test_property():
    root   = Node(model, '')
    image  = Node(model, 'functions/image')
    plot   = Node(model, 'plots/evolution')
    field  = Node(model, 'exports/field')
    vector = Node(model, 'exports/vector')
    # Test conversion to and from 'Boolean'.
    old = image.property('flipx')
    image.property('flipx', False)
    assert image.property('flipx') is False
    image.property('flipx', old)
    assert image.property('flipx') == old
    # Test conversion to and from 'Double'.
    old = image.property('xmin')
    image.property('xmin', -10.0)
    assert isclose(image.property('xmin'), -10)
    image.property('xmin', old)
    assert isclose(image.property('xmin'), old)
    # Test conversion to and from 'DoubleArray'.
    old = field.property('outersolnumindices')
    new = array([1.0, 2.0, 3.0])
    field.property('outersolnumindices', new)
    assert isclose(field.property('outersolnumindices'), new).all()
    field.property('outersolnumindices', old)
    assert isclose(field.property('outersolnumindices'), old).all()
    # Test conversion to and from 'File'.
    old = image.property('filename')
    image.property('filename', Path('new.tif'))
    assert image.property('filename') == Path('new.tif')
    image.property('filename', old)
    assert image.property('filename') == old
    # Test conversion to and from 'Int'.
    old = image.property('refreshcount')
    image.property('refreshcount', 1)
    assert image.property('refreshcount') == 1
    image.property('refreshcount', old)
    assert image.property('refreshcount') == old
    # Test conversion to and from 'IntArray'.
    old = plot.property('solnum')
    new = array([1, 2, 3])
    plot.property('solnum', new)
    assert (plot.property('solnum') == new).all()
    plot.property('solnum', old)
    assert (plot.property('solnum') == old).all()
    # Test conversion from 'None'.
    none = image.property('exportfilename')
    assert none is None
    # Test conversion to and from 'String'.
    old = image.property('funcname')
    image.property('funcname', 'new')
    assert image.property('funcname') == 'new'
    image.property('funcname', old)
    assert image.property('funcname') == old
    # Test conversion to and from 'StringArray'.
    old = vector.property('descr')
    vector.property('descr', ['x', 'y', 'z'])
    assert vector.property('descr') == ['x', 'y', 'z']
    vector.property('descr', old)
    assert vector.property('descr') == old
    # Test conversion to and from 'StringMatrix'.
    old = plot.property('plotonsecyaxis')
    new = [['medium 1', 'on', 'ptgr1'], ['medium 2', 'on', 'ptgr2']]
    plot.property('plotonsecyaxis', new)
    assert plot.property('plotonsecyaxis') == new
    plot.property('plotonsecyaxis', old)
    assert plot.property('plotonsecyaxis') == old
    # Read and write back every node property in the model.
    if not client.port:
        # Skip test in client-server mode where it's excruciatingly slow.
        test_rewrite(root)


def test_properties():
    step = Node(model, 'functions/step')
    assert 'funcname' in step.properties()
    assert 'funcname' in step.properties().keys()
    assert 'step' in step.properties().values()
    assert ('funcname', 'step') in step.properties().items()


def test_toggle():
    node = Node(model, 'functions/step')
    assert node.java.isActive()
    node.toggle()
    assert not node.java.isActive()
    node.toggle()
    assert node.java.isActive()
    node.toggle('off')
    assert not node.java.isActive()
    node.toggle('on')
    assert node.java.isActive()


def test_run():
    study = Node(model, 'studies/static')
    solution = Node(model, 'solutions/electrostatic solution')
    assert solution.java.isEmpty()
    study.run()
    assert not solution.java.isEmpty()


def test_create():
    functions = Node(model, 'functions')
    functions.create('Analytic')
    assert (functions/'Analytic 1').exists()
    functions.create('Analytic', name='f')
    assert (functions/'f').exists()


def test_remove():
    functions = Node(model, 'functions')
    assert (functions/'Analytic 1').exists()
    (functions/'Analytic 1').remove()
    assert not (functions/'Analytic 1').exists()
    assert (functions/'f').exists()
    (functions/'f').remove()
    assert not (functions/'f').exists()


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'stand-alone' in arguments:
        mph.option('session', 'stand-alone')
    if 'client-server' in arguments:
        mph.option('session', 'client-server')
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG if 'debug' in arguments else logging.INFO,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    setup_module()
    try:

        test_parse()
        test_join()
        test_escape()
        test_unescape()

        test_init()
        test_str()
        test_repr()
        test_eq()
        test_truediv()
        test_contains()
        test_iter()
        test_java()

        test_name()
        test_tag()
        test_parent()
        test_children()
        test_is_root()
        test_is_group()
        test_exists()

        test_rename()
        test_property()
        test_properties()
        test_toggle()
        test_run()
        test_create()
        test_remove()

    finally:
        teardown_module()
