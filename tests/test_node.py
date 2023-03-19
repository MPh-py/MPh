"""Tests the `node` module."""

########################################
# Dependencies                         #
########################################
import mph
from mph import node, Node
import models
from fixtures import logging_disabled
from fixtures import capture_stdout
from fixtures import setup_logging
from pytest import raises
from pathlib import Path
from numpy import array, isclose
from textwrap import dedent


########################################
# Fixtures                             #
########################################
client = None
model  = None


def setup_module():
    global client, model
    client = mph.start()
    model = models.capacitor()


########################################
# Tests                                #
########################################

def test_init():
    node = Node(model, '')
    assert node.model == model
    node = Node(model, 'functions')
    assert node.model == model
    assert 'function' in node.alias
    assert 'functions' in node.alias.values()
    assert 'functions' in node.groups
    assert 'self.model.java.func()' in node.groups.values()
    Node(model, node)
    with logging_disabled():
        with raises(TypeError):
            Node(model, False)


def test_str():
    assert str(Node(model, 'functions/step')) == 'functions/step'


def test_repr():
    assert repr(Node(model, 'functions/step')) == "Node('functions/step')"


def test_eq():
    assert Node(model, 'function/step') == Node(model, '/functions/step/')


def test_truediv():
    assert Node(model, 'functions')/'step' == Node(model, 'functions/step')
    with logging_disabled():
        with raises(TypeError):
            Node(model, 'functions')/False


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
    if not node.is_root() and (other/node).exists():
        assert node.tag() == (other/node).tag()
    for child in node:
        compare_tags(child, other)


def test_tag():
    assert Node(model, 'functions/step').tag() == 'step1'
    if not client.port:
        # Skip test in client-server mode where it's fairly slow.
        here = Path(__file__).resolve().parent
        demo = client.load(here/'demo.mph')
        demo.solve()
        root = Node(model, '')
        compare_tags(root, demo)


def test_type():
    assert Node(model, 'functions/step').type() == 'Step'


def test_parent():
    assert Node(model, '').parent() is None
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


def test_comment():
    node = Node(model, 'datasets/sweep//solution')
    assert node.exists()
    text = node.comment()
    assert text
    node.comment('test')
    assert node.comment() == 'test'
    node.comment('')
    assert node.comment() == ''
    node.comment(text)
    assert node.comment() == text
    with logging_disabled(), raises(LookupError):
        node = Node(model, 'functions/non-existing')
        node.comment('test')


def test_problems():
    # Test errors and warnings in geometry sequence.
    root = Node(model, '')
    geometry = root/'geometries/geometry'
    rounded = geometry/'rounded'
    geometry.java.run((geometry/'rounded').tag())
    empty = geometry.create('ExplicitSelection', name='empty')
    empty.java.selection('selection').set('fil1(1)', 1)
    geometry.run()
    empty.java.selection('selection').clear()
    geometry.run()
    rounded.java.selection('point').clear()
    try:
        geometry.run()
    except Exception:
        pass
    problems = root.problems()
    assert problems
    rounded_has_error = False
    for problem in problems:
        if problem['node'] == rounded and problem['category'] == 'error':
            rounded_has_error = True
            break
    assert rounded_has_error
    empty_has_warning = False
    for problem in problems:
        if problem['node'] == empty and problem['category'] == 'warning':
            empty_has_warning = True
            break
    assert empty_has_warning
    empty.remove()
    vertices = geometry/'vertices'
    rounded.java.selection('point').named(vertices.tag())
    geometry.run()
    assert not root.problems()
    # Test errors and warnings in mesh sequence.
    root = Node(client.create('mesh_problems'), None)
    (root/'components').create(True, name='component')
    geometry = (root/'geometries').create(3, name='geometry')
    cylinder1 = geometry.create('Cylinder', name='cylinder 1')
    cylinder1.property('h', 3.0)
    cylinder2 = geometry.create('Cylinder', name='cylinder 2')
    cylinder2.property('h', 3.0)
    cylinder2.property('r', 0.95)
    difference = geometry.create('Difference', name='difference')
    difference.java.selection('input').set(cylinder1.tag())
    difference.java.selection('input2').set(cylinder2.tag())
    mesh = (root/'meshes').create(geometry, name='mesh')
    size = mesh/'Size'
    size.property('hauto', 9)
    surface = mesh.create('FreeTri', name='surface')
    surface.java.selection().geom(2).set(1, 2, 7, 10)
    volume = mesh.create('FreeTet', name='volume')
    volume.create('Size', name='size')
    try:
        mesh.run()
    except Exception:
        pass
    problems = root.problems()
    assert problems
    assert len(problems) == 5
    assert all([problem['message'] for problem in problems])
    assert any([problem['category'] == 'error' for problem in problems])
    assert any([problem['category'] == 'warning' for problem in problems])
    assert all([problem['node'] == volume for problem in problems])
    assert all([problem['selection'] for problem in problems])
    # Test error in solver sequence.
    root = Node(model, '')
    anode = root/'physics'/'electrostatic'/'anode'
    anode.property('V0', '+Ua/2')
    study = root/'studies'/'static'
    try:
        study.run()
    except Exception:
        pass
    problems = root.problems()
    assert problems
    solver_has_error = False
    solver = root/'solutions'/'electrostatic solution'/'stationary solver'
    for problem in problems:
        if problem['node'] == solver and problem['category'] == 'error':
            solver_has_error = True
            break
    assert solver_has_error
    assert 'Undefined variable' in problem['message']
    assert not problem['selection']
    anode.property('V0', '+U/2')
    study.run()
    assert not root.problems()
    solver.parent().java.clearSolution()


def test_rename():
    with logging_disabled():
        with raises(PermissionError):
            Node(model, '').rename('something')
        with raises(PermissionError):
            Node(model, 'functions').rename('something')
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


def test_retag():
    with logging_disabled():
        with raises(PermissionError):
            Node(model, '').retag('something')
        with raises(PermissionError):
            Node(model, 'functions').retag('something')
        with raises(Exception):
            Node(model, 'functions/non-existing').retag('something')
    node = Node(model, 'functions/step')
    old = node.tag()
    node.retag('new')
    assert node.tag() == 'new'
    node.retag(old)
    assert node.tag() == old


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
    # Test changing material properties.
    assert (material/'Basic').property('relpermittivity') == ['1']
    (material/'Basic').property('relpermittivity', 2)
    assert (material/'Basic').property('relpermittivity') == ['2']
    # Read and write back every node property in the model.
    if not client.port:
        # Skip test in client-server mode where it's excruciatingly slow.
        rewrite_properties(root)


def test_properties():
    assert Node(model, 'functions').properties() == {}
    function = Node(model, 'functions/step')
    assert 'funcname' in function.properties()
    assert 'funcname' in function.properties().keys()
    assert 'step' in function.properties().values()
    assert ('funcname', 'step') in function.properties().items()


def test_select():
    with logging_disabled():
        with raises(LookupError):
            Node(model, 'selections/non-existing').select(None)
        with raises(NotImplementedError):
            Node(model, 'geometries/geometry/rounded').select(None)
        with raises(TypeError):
            Node(model, 'parameters').select(None)
        with raises(TypeError):
            Node(model, 'functions/step').select(None)
        with raises(TypeError):
            Node(model, 'selections/domains').select(Node(model, ''))
        cathode = Node(model, 'physics/electrostatic/cathode')
        with raises(LookupError):
            cathode.select(Node(model, 'selections/non-existing'))
        with raises(ValueError):
            cathode.select('invalid argument')


def test_selection():
    cathode = Node(model, 'physics/electrostatic/cathode')
    surface = Node(model, 'selections/cathode surface')
    cathode.select(surface)
    assert cathode.selection() == surface
    cathode.select([1, 2, 3])
    assert (cathode.selection() == array([1, 2, 3])).all()
    cathode.select(array([1, 2, 3]))
    assert (cathode.selection() == array([1, 2, 3])).all()
    cathode.select(1)
    assert (cathode.selection() == array([1])).all()
    cathode.select(array([1])[0])
    assert (cathode.selection() == array([1])).all()
    cathode.select(None)
    assert cathode.selection() is None
    cathode.select('all')
    assert (cathode.selection() == array(range(1, 27))).all()
    domains = Node(model, 'selections/domains')
    assert (domains.selection() == array([1, 2, 3, 4])).all()
    domains.select([1, 2, 3])
    assert (domains.selection() == array([1, 2, 3])).all()
    domains.select(None)
    assert domains.selection() is None
    domains.select('all')
    assert (domains.selection() == array([1, 2, 3, 4])).all()
    with logging_disabled():
        with raises(LookupError):
            Node(model, 'selections/non-existing').selection()
        with raises(NotImplementedError):
            Node(model, 'geometries/geometry/rounded').selection()
        with raises(TypeError):
            Node(model, 'parameters').selection()
        with raises(TypeError):
            Node(model, 'functions/step').selection()


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
    assert not Node(model, 'functions/non-existing').exists()
    with logging_disabled():
        with raises(LookupError):
            Node(model, 'functions/non-existing').toggle()


def test_run():
    study = Node(model, 'studies/static')
    solution = Node(model, 'solutions/electrostatic solution')
    assert solution.java.isEmpty()
    study.run()
    assert not solution.java.isEmpty()
    with logging_disabled():
        with raises(LookupError):
            Node(model, 'functions/non-existing').run()
        with raises(RuntimeError):
            Node(model, 'functions').run()


def test_import():
    # Skip here as we will test this for the `Model` class anyway and
    # would have to create nodes first, which is the test to follow.
    pass


def test_create():
    functions = Node(model, 'functions')
    functions.create('Analytic')
    assert (functions/'Analytic 1').exists()
    functions.create('Analytic', name='f')
    assert (functions/'f').exists()
    geometry = Node(model, 'geometries/geometry')
    physics = Node(model, 'physics')
    physics.create('Electrostatics', geometry)
    with logging_disabled():
        with raises(PermissionError):
            Node(model, '').create()
        with raises(RuntimeError):
            Node(model, 'components/component').create()
    material = Node(model, 'materials/medium 1')
    material.create('custom', name='custom')
    assert (material/'custom').exists()
    (material/'custom').property('bulkviscosity', '1')
    assert (material/'custom').property('bulkviscosity') == '1'


def test_remove():
    functions = Node(model, 'functions')
    assert (functions/'Analytic 1').exists()
    (functions/'Analytic 1').remove()
    assert not (functions/'Analytic 1').exists()
    assert (functions/'f').exists()
    (functions/'f').remove()
    assert not (functions/'f').exists()
    physics = Node(model, 'physics')
    (physics/'Electrostatics 1').remove()
    assert not (physics/'Electrostatics 1').exists()
    material = Node(model, 'materials/medium 1')
    (material/'custom').remove()
    assert not (material/'custom').exists()
    with logging_disabled():
        with raises(PermissionError):
            Node(model, '').remove()
        with raises(PermissionError):
            Node(model, 'function').remove()
        with raises(LookupError):
            Node(model, 'function/non-existing').remove()


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


def test_load_patterns():
    tags = node.load_patterns()
    assert 'physics → Electrostatics' in tags.keys()
    assert 'es' in tags.values()


def test_feature_path():
    assert node.feature_path(model/'functions') == ['functions']
    assert node.feature_path(model/'functions/step') == ['functions', 'Step']
    assert node.feature_path(model/'meshes'/'mesh') == ['meshes', '?']


def test_tag_pattern():
    assert node.tag_pattern(['functions'])            == 'func'
    assert node.tag_pattern(['functions', 'Step'])    == 'step*'
    assert node.tag_pattern(['non-existing', 'Step']) == 'ste*'
    assert node.tag_pattern(['non-existing', '?'])    == 'tag*'


def test_cast():
    bool_array_1d = array([True, False])
    bool_array_2d = array([[True, False], [False, True]])
    assert node.cast(bool_array_1d).__class__.__name__ == 'boolean[]'
    assert node.cast(bool_array_2d).__class__.__name__ == 'boolean[][]'
    with logging_disabled():
        with raises(TypeError):
            array3d = array([[[1,2], [3,4]], [[5,6], [7,8]]], dtype=object)
            node.cast(array3d)
        with raises(TypeError):
            three_rows = array([[1,2], [3,4], [5,6]], dtype=object)
            node.cast(three_rows)
        with raises(TypeError):
            node.cast(array([1+1j, 1-1j]))
        with raises(TypeError):
            node.cast({1, 2, 3})


def test_get():
    pass


def test_tree():
    with capture_stdout() as output:
        mph.tree(model, max_depth=1)
    expected = '''
        capacitor
        ├─ parameters
        ├─ functions
        ├─ components
        ├─ geometries
        ├─ views
        ├─ selections
        ├─ coordinates
        ├─ variables
        ├─ couplings
        ├─ physics
        ├─ multiphysics
        ├─ materials
        ├─ meshes
        ├─ studies
        ├─ solutions
        ├─ batches
        ├─ datasets
        ├─ evaluations
        ├─ tables
        ├─ plots
        └─ exports
    '''
    assert output.text().strip() == dedent(expected).strip()
    with capture_stdout() as output:
        mph.tree(model/'materials')
    expected = '''
        materials
        ├─ medium 1
        │  └─ Basic
        └─ medium 2
           └─ Basic
    '''
    assert output.text().strip() == dedent(expected).strip()


def test_inspect():
    node = Node(model, 'datasets/sweep//solution')
    node.toggle('off')
    with capture_stdout() as output:
        mph.inspect(node)
    assert output.text().strip().startswith('name:')


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    setup_module()

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

    test_comment()
    test_problems()

    test_rename()
    test_property()
    test_properties()
    test_select()
    test_selection()
    test_toggle()
    test_run()
    test_import()
    test_create()
    test_remove()

    test_parse()
    test_join()
    test_escape()
    test_unescape()

    test_load_patterns()
    test_feature_path()
    test_tag_pattern()

    test_cast()
    test_get()
    test_tree()
    test_inspect()
