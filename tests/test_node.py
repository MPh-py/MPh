"""Tests the `node` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from mph import node, Node
from models import capacitor
from pathlib import Path
from numpy import array, isclose
from sys import argv
import logging


########################################
# Fixtures                             #
########################################
client = None
model  = None


def setup_module():
    global client, model
    client = mph.start()
    model = capacitor()


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


def test_java():
    assert Node(model, 'functions').java
    assert Node(model, 'functions/step').java


def test_name():
    assert Node(model, 'functions').name() == 'functions'
    assert Node(model, 'functions/step').name() == 'step'


def compare_tags(node, other):
    assert (other/node).exists()
    assert node.tag() == (other/node).tag() or node.is_root()
    for child in node:
        compare_tags(child, other)


def test_tag():
    assert Node(model, 'functions/step').tag() == 'step1'
    if not client.port:
        # Skip test in client-server mode where it's fairly slow.
        here = Path(__file__).resolve().parent
        demo = client.load(here.parent/'demos'/'capacitor.mph')
        demo.solve()
        root = Node(model, '')
        compare_tags(root, demo)


def test_type():
    assert Node(model, 'functions/step').type() == 'Step'


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


def rewrite_properties(node):
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
        rewrite_properties(child)


def test_property():
    root     = Node(model, '')
    function = root/'functions'/'step'
    axis     = root/'geometries'/'geometry'/'axis'
    material = root/'materials'/'medium 1'
    plot     = root/'plots'/'evolution'
    export   = root/'exports'/'data'
    # Test conversion to and from 'Boolean'.
    old = function.property('smoothactive')
    function.property('smoothactive', False)
    assert function.property('smoothactive') is False
    function.property('smoothactive', old)
    assert function.property('smoothactive') == old
    # Test conversion to and from 'Double'.
    old = function.property('location')
    function.property('location', -10.0)
    assert isclose(function.property('location'), -10)
    function.property('location', old)
    assert isclose(function.property('location'), old)
    # Test conversion to and from 'DoubleArray'.
    old = export.property('outersolnumindices')
    new = array([1.0, 2.0, 3.0])
    export.property('outersolnumindices', new)
    assert isclose(export.property('outersolnumindices'), new).all()
    export.property('outersolnumindices', old)
    assert isclose(export.property('outersolnumindices'), old).all()
    # Test conversion to and from 'File'.
    old = export.property('filename')
    export.property('filename', Path('new.tif'))
    assert export.property('filename') == Path('new.tif')
    export.property('filename', old)
    assert export.property('filename') == old
    # Test conversion to and from 'Int'.
    old = plot.property('axisprecision')
    plot.property('axisprecision', 4)
    assert plot.property('axisprecision') == 4
    plot.property('axisprecision', old)
    assert plot.property('axisprecision') == old
    # Test conversion to and from 'IntArray'.
    old = axis.property('segid')
    new = array([1, 2, 3], dtype=int)
    axis.property('segid', new)
    assert (axis.property('segid') == new).all()
    axis.property('segid', old)
    assert (axis.property('segid') == old).all()
    # Test conversion from 'None'.
    assert material.property('customize') is None
    # Test conversion to and from 'String'.
    old = function.property('funcname')
    function.property('funcname', 'new')
    assert function.property('funcname') == 'new'
    function.property('funcname', old)
    assert function.property('funcname') == old
    # Test conversion to and from 'StringArray'.
    old = export.property('descr')
    export.property('descr', ['x', 'y', 'z'])
    assert export.property('descr') == ['x', 'y', 'z']
    export.property('descr', old)
    assert export.property('descr') == old
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
        rewrite_properties(root)


def test_properties():
    function = Node(model, 'functions/step')
    assert 'funcname' in function.properties()
    assert 'funcname' in function.properties().keys()
    assert 'step' in function.properties().values()
    assert ('funcname', 'step') in function.properties().items()


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
