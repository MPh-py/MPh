"""Tests the model class."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from pathlib import Path
from numpy import array, isclose
from sys import argv
import logging
import warnings


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
    client.clear()
    here = Path(__file__).parent
    for suffix in ('mph', 'java', 'm', 'vba'):
        file = here/f'model.{suffix}'
        if file.exists():
            file.unlink()
    file = here/'model2.mph'
    if file.exists():
        file.unlink()
    for name in ('field.txt', 'field2.txt', 'vector.txt', 'vector.vtu'):
        file = here/name
        if file.exists():
            file.unlink()


########################################
# Tests                                #
########################################

def test_str():
    assert str(model) == 'capacitor'


def test_repr():
    assert repr(model) == "Model('capacitor')"


def test_eq():
    assert model == model


def test_truediv():
    assert (model/'functions').name() == 'functions'
    node = model/'functions'/'step'
    assert (model/node).name() == 'step'
    assert (model/None).is_root()


def test_name():
    assert model.name() == 'capacitor'


def test_file():
    assert model.file().name == 'capacitor.mph'


def test_functions():
    assert 'step'  in model.functions()
    assert 'image' in model.functions()
    assert 'table' in model.functions()


def test_components():
    assert 'component' in model.components()


def test_geometries():
    assert 'geometry' in model.geometries()


def test_selections():
    assert 'domains'  in model.selections()
    assert 'exterior' in model.selections()
    assert 'axis'     in model.selections()
    assert 'center'   in model.selections()


def test_physics():
    assert 'electrostatic'     in model.physics()
    assert 'electric currents' in model.physics()


def test_multiphysics():
    assert model.multiphysics() == []


def test_materials():
    materials = model.materials()
    assert 'medium 1' in materials
    assert 'medium 2' in materials


def test_meshes():
    assert 'mesh' in model.meshes()


def test_studies():
    assert 'static'     in model.studies()
    assert 'relaxation' in model.studies()
    assert 'sweep'      in model.studies()


def test_solutions():
    assert 'electrostatic solution'  in model.solutions()
    assert 'time-dependent solution' in model.solutions()
    assert 'parametric solutions'    in model.solutions()


def test_datasets():
    assert 'electrostatic'    in model.datasets()
    assert 'time-dependent'   in model.datasets()
    assert 'parametric sweep' in model.datasets()


def test_plots():
    assert 'electrostatic field'  in model.plots()
    assert 'time-dependent field' in model.plots()
    assert 'evolution'            in model.plots()
    assert 'sweep'                in model.plots()


def test_exports():
    assert 'field' in model.exports()


def test_build():
    model.build()


def test_mesh():
    model.mesh()


def test_solve():
    model.solve()


def test_evaluate():
    # Test global evaluation of stationary solution.
    C = model.evaluate('2*es.intWe/U^2', 'pF')
    assert abs(C - 0.74) < 0.01
    # Test local evaluation of stationary solution.
    (x, y, E) = model.evaluate(['x', 'y', 'es.normE'], ['mm', 'mm', 'V/m'])
    (Emax, xmax, ymax) = (E.max(), x[E.argmax()], y[E.argmax()])
    assert abs(Emax - 818) < 5
    assert abs(abs(xmax) - 1.04) < 0.01
    assert abs(abs(ymax) - 4.27) < 0.01
    # Test global evaluation of time-dependent solution.
    (dataset, expression, unit) = ('time-dependent', '2*ec.intWe/U^2', 'pF')
    (indices, values) = model.inner(dataset)
    assert values[0] == 0
    assert values[-1] == 1
    Cf = model.evaluate(expression, unit, dataset, 'first')
    assert abs(Cf - 0.74) < 0.01
    Cl = model.evaluate(expression, unit, dataset, 'last')
    assert abs(Cl - 0.83) < 0.01
    C = model.evaluate(expression, unit, dataset)
    assert C[0] == Cf
    assert C[-1] == Cl
    # Test local evaluation of time-dependent solution.
    (dataset, expression, unit) = ('time-dependent', 'ec.normD', 'nC/m^2')
    Df = model.evaluate(expression, unit, dataset, 'first')
    assert abs(Df.max() -  7.2) < 0.1
    Dl = model.evaluate(expression, unit, dataset, 'last')
    assert abs(Dl.max() - 10.8) < 0.1
    D = model.evaluate(expression, unit, dataset)
    assert D[0].max()  == Df.max()
    assert D[-1].max() == Dl.max()
    # Test global evaluation of parameter sweep.
    (dataset, expression, unit) = ('parametric sweep', '2*ec.intWe/U^2', 'pF')
    (indices, values) = model.outer(dataset)
    for (index, value) in zip(indices, values):
        C = model.evaluate(expression, unit, dataset, 'first', index)
        if value == 1:
            assert abs(C - 1.32) < 0.01
        elif value == 2:
            assert abs(C - 0.74) < 0.01
        elif value == 3:
            assert abs(C - 0.53) < 0.01
        else:
            raise ValueError(f'Unexpected value {value} for parameter d."')
    # Test local evaluation of parameter sweep.
    for (index, value) in zip(indices, values):
        if value == 2:
            break
    else:
        raise ValueError('Could not find solution for d = 2 mm."')
    (dataset, expression, unit) = ('parametric sweep', 'ec.normD', 'nC/m^2')
    Df = model.evaluate(expression, unit, dataset, 'first', index)
    assert abs(Df.max() -  7.2) < 0.1
    Dl = model.evaluate(expression, unit, dataset, 'last', index)
    assert abs(Dl.max() - 10.8) < 0.1
    D = model.evaluate(expression, unit, dataset, outer=index)
    assert D[0].max()  == Df.max()
    assert D[-1].max() == Dl.max()


def test_rename():
    name = model.name()
    model.rename('test')
    assert model.name() == 'test'
    model.rename(name)
    assert model.name() == name


def test_parameters():
    parameters = model.parameters()
    names = [parameter.name for parameter in parameters]
    assert 'U' in names
    assert 'd' in names
    assert 'l' in names
    assert 'w' in names


def test_parameter():
    value = model.parameter('U')
    model.parameter('U', '2[V]')
    assert model.parameter('U') == '2[V]'
    model.parameter('U', '2', 'V')
    assert model.parameter('U') == '2 [V]'
    model.parameter('U', '2')
    assert model.parameter('U') == '2'
    assert model.parameter('U', evaluate=True) == 2
    model.parameter('U', value)
    assert model.parameter('U') == value
    model.parameter('U', description='test')
    names = [p.name for p in model.parameters()]
    descriptions = [p.description for p in model.parameters()]
    assert descriptions[names.index('U')] == 'test'


def test_properties():
    assert 'flipx' in model.properties('functions/image')


def test_property():
    # Test conversion to and from 'Boolean'.
    old = model.property('functions/image', 'flipx')
    model.property('functions/image', 'flipx', False)
    assert model.property('functions/image', 'flipx') is False
    model.property('functions/image', 'flipx', old)
    assert model.property('functions/image', 'flipx') == old
    # Test conversion to and from 'Double'.
    old = model.property('functions/image', 'xmin')
    model.property('functions/image', 'xmin', -10.0)
    assert isclose(model.property('functions/image', 'xmin'), -10)
    model.property('functions/image', 'xmin', old)
    assert isclose(model.property('functions/image', 'xmin'), old)
    # Test conversion to and from 'DoubleArray'.
    old = model.property('exports/field', 'outersolnumindices')
    new = array([1.0, 2.0, 3.0])
    model.property('exports/field', 'outersolnumindices', new)
    assert isclose(model.property('exports/field', 'outersolnumindices'),
                   new).all()
    model.property('exports/field', 'outersolnumindices', old)
    assert isclose(model.property('exports/field', 'outersolnumindices'),
                   old).all()
    # Test conversion to and from 'File'.
    old = model.property('functions/image', 'filename')
    model.property('functions/image', 'filename', Path('new.tif'))
    assert model.property('functions/image', 'filename') == Path('new.tif')
    model.property('functions/image', 'filename', old)
    assert model.property('functions/image', 'filename') == old
    # Test conversion to and from 'Int'.
    old = model.property('functions/image', 'refreshcount')
    model.property('functions/image', 'refreshcount', 1)
    assert model.property('functions/image', 'refreshcount') == 1
    model.property('functions/image', 'refreshcount', old)
    assert model.property('functions/image', 'refreshcount') == old
    # Test conversion to and from 'IntArray'.
    old = model.property('plots/evolution', 'solnum')
    new = array([1, 2, 3])
    model.property('plots/evolution', 'solnum', new)
    assert (model.property('plots/evolution', 'solnum') == new).all()
    model.property('plots/evolution', 'solnum', old)
    assert (model.property('plots/evolution', 'solnum') == old).all()
    # Test conversion from 'None'.
    none = model.property('functions/image', 'exportfilename')
    assert none is None
    # Test conversion to and from 'String'.
    old = model.property('functions/image', 'funcname')
    model.property('functions/image', 'funcname', 'new')
    assert model.property('functions/image', 'funcname') == 'new'
    model.property('functions/image', 'funcname', old)
    assert model.property('functions/image', 'funcname') == old
    # Test conversion to and from 'StringArray'.
    old = model.property('exports/vector', 'descr')
    model.property('exports/vector', 'descr', ['x', 'y', 'z'])
    assert model.property('exports/vector', 'descr') == ['x', 'y', 'z']
    model.property('exports/vector', 'descr', old)
    assert model.property('exports/vector', 'descr') == old
    # Test conversion to and from 'StringMatrix'.
    old = model.property('plots/evolution', 'plotonsecyaxis')
    new = [['medium 1', 'on', 'ptgr1'], ['medium 2', 'on', 'ptgr2']]
    model.property('plots/evolution', 'plotonsecyaxis', new)
    assert model.property('plots/evolution', 'plotonsecyaxis') == new
    model.property('plots/evolution', 'plotonsecyaxis', old)
    assert model.property('plots/evolution', 'plotonsecyaxis') == old


def test_create():
    model.create('functions/interpolation', 'Interpolation')
    assert 'interpolation' in model.functions()


def test_remove():
    model.remove('functions/interpolation')
    assert 'interpolation' not in model.functions()


def test_import():
    # Import image with file name specified as string and Path.
    here = Path(__file__).parent
    image = model/'functions'/'image'
    assert image.property('sourcetype') == 'model'
    image.java.discardData()
    assert image.property('sourcetype') == 'user'
    model.import_(image, 'gaussian.tif')
    assert image.property('sourcetype') == 'model'
    image.java.discardData()
    assert image.property('sourcetype') == 'user'
    model.import_(image, here/'gaussian.tif')
    assert image.property('sourcetype') == 'model'
    # Solve with pre-defined boundary condition.
    model.solve('static')
    table = model/'functions'/'table'
    assert table.property('table')[0] == ['+1', '+2']
    assert table.property('funcname') == 'f'
    old_table = table.property('table')
    old_V0 = model.property('physics/electrostatic/anode', 'V0')
    (y, E) = model.evaluate(['y', 'es.normE'])
    (E_pre, y_pre) = (E.max(), y[E.argmax()])
    # Apply interpolation table defined in model.
    model.property('physics/electrostatic/anode', 'V0', 'U/2 * f(y/l)')
    model.solve('static')
    (y, E) = model.evaluate(['y', 'es.normE'])
    (E_up, y_up) = (E.max(), y[E.argmax()])
    # Import interpolation table with data flipped upside down.
    model.import_(table, here/'table.txt')
    assert table.property('table')[0] == ['+1', '-2']
    table.property('funcname', 'f')
    model.solve('static')
    (y, E) = model.evaluate(['y', 'es.normE'])
    (E_down, y_down) = (E.max(), y[E.argmax()])
    assert E_up - E_down < (E_up + E_down)/1000
    assert y_up + y_down < (y_up - y_down)/1000
    # Re-apply original boundary condition.
    model.property('physics/electrostatic/anode', 'V0', old_V0)
    assert model.property('physics/electrostatic/anode', 'V0') == old_V0
    table.property('table', old_table)
    assert table.property('table') == old_table
    assert table.property('funcname') == 'f'
    model.solve('static')
    (y, E) = model.evaluate(['y', 'es.normE'])
    (E_re, y_re) = (E.max(), y[E.argmax()])
    assert (E_re - E_pre) < 1
    assert (y_re - y_pre) < 0.001


def test_export():
    here = Path(__file__).parent
    assert not (here/'field.txt').exists()
    model.export('field')
    assert (here/'field.txt').exists()
    (here/'field.txt').unlink()
    assert not (here/'field.txt').exists()
    model.export('exports/field')
    assert (here/'field.txt').exists()
    (here/'field.txt').unlink()
    assert not (here/'field.txt').exists()
    model.export(model/'exports'/'field')
    assert (here/'field.txt').exists()
    (here/'field.txt').unlink()
    assert not (here/'field.txt').exists()
    assert not (here/'field2.txt').exists()
    model.export('exports/field', here/'field2.txt')
    assert (here/'field2.txt').exists()
    (here/'field2.txt').unlink()
    assert not (here/'vector.txt').exists()
    model.property('exports/vector', 'exporttype', 'text')
    model.export('exports/vector', here/'vector.txt')
    assert (here/'vector.txt').exists()
    (here/'vector.txt').unlink()
    assert not (here/'vector.vtu').exists()
    model.property('exports/vector', 'exporttype', 'vtu')
    model.export('exports/vector', here/'vector.vtu')
    assert (here/'vector.vtu').exists()
    (here/'vector.vtu').unlink()


def test_clear():
    model.clear()


def test_reset():
    model.reset()


def test_save():
    here = Path(__file__).parent
    model.save(here/'model.mph')
    assert (here/'model.mph').exists()
    model.save(str(here/'model2.mph'))
    assert (here/'model2.mph').exists()
    assert (here/'model.mph').read_text(errors='ignore').startswith('PK')
    model.save(here/'model.java')
    assert (here/'model.java').exists()
    assert 'public static void main' in (here/'model.java').read_text()
    model.save(here/'model.m')
    assert (here/'model.m').exists()
    assert 'function out = model' in (here/'model.m').read_text()
    model.save(here/'model.vba')
    assert (here/'model.vba').exists()
    assert 'Sub run()' in (here/'model.vba').read_text()


def test_features():
    assert 'Laplace equation' in model.features('electrostatic')
    assert 'zero charge'      in model.features('electrostatic')
    assert 'initial values'   in model.features('electrostatic')
    assert 'anode'            in model.features('electrostatic')
    assert 'cathode'          in model.features('electrostatic')


def test_toggle():
    model.solve('static')
    assert abs(model.evaluate('V_es').mean()) < 0.1
    model.toggle('electrostatic', 'cathode')
    model.solve('static')
    assert abs(model.evaluate('V_es').mean() - 0.5) < 0.1
    model.toggle('electrostatic', 'cathode', 'on')
    model.solve('static')
    assert abs(model.evaluate('V_es').mean()) < 0.1
    model.toggle('electrostatic', 'cathode', 'off')
    model.solve('static')
    assert abs(model.evaluate('V_es').mean() - 0.5) < 0.1


def test_load():
    model.load('gaussian.tif', 'image')


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

        test_str()
        test_repr()
        test_eq()
        test_truediv()

        test_name()
        test_file()
        test_functions()
        test_components()
        test_geometries()
        test_selections()
        test_physics()
        test_multiphysics()
        test_materials()
        test_meshes()
        test_studies()
        test_solutions()
        test_datasets()
        test_plots()
        test_exports()

        test_build()
        test_mesh()
        test_solve()

        test_evaluate()

        test_rename()
        test_parameters()
        test_parameter()
        test_properties()
        test_property()
        test_create()
        test_remove()

        test_import()
        test_export()
        test_clear()
        test_reset()
        test_save()

        warnings.simplefilter('ignore')
        test_features()
        test_toggle()
        test_load()

    finally:
        teardown_module()
