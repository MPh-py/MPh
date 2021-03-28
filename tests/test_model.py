"""Tests the model class."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent
import mph
from sys import argv
from pathlib import Path
import logging
from numpy import array, isclose


########################################
# Fixtures                             #
########################################
client = None
server = None
model  = None
here   = Path(__file__).parent
file   = here/'capacitor.mph'
saveas = here/'temp'


def setup_module():
    global client, model
    client = mph.start()
    model = client.load(file)


def teardown_module():
    client.clear()
    for suffix in ['.mph', '.java', '.m', '.vba']:
        file = saveas.with_suffix(suffix)
        if file.exists():
            file.unlink()


########################################
# Tests                                #
########################################

def test_name():
    assert model.name() == 'capacitor'


def test_parameters():
    parameters = model.parameters()
    names = [parameter.name for parameter in parameters]
    assert 'U' in names
    assert 'd' in names
    assert 'l' in names
    assert 'w' in names


def test_functions():
    functions = model.functions()
    assert 'test_function' in functions


def test_components():
    assert 'component' in model.components()


def test_geometries():
    assert 'geometry' in model.geometries()


def test_selections():
    selections = model.selections()
    assert 'domains' in selections
    assert 'exterior' in selections
    assert 'axis' in selections
    assert 'center' in selections


def test_physics():
    physics = model.physics()
    assert 'electrostatic' in physics
    assert 'electric currents' in physics


def test_features():
    features = model.features('electrostatic')
    assert 'Laplace equation' in features
    assert 'zero charge' in features
    assert 'initial values' in features
    assert 'anode' in features
    assert 'cathode' in features


def test_materials():
    materials = model.materials()
    assert 'medium 1' in materials
    assert 'medium 2' in materials


def test_meshes():
    assert 'mesh' in model.meshes()


def test_studies():
    studies = model.studies()
    assert 'static' in studies
    assert 'relaxation' in studies
    assert 'sweep' in studies


def test_solutions():
    solutions = model.solutions()
    assert 'electrostatic solution' in solutions
    assert 'time-dependent solution' in solutions
    assert 'parametric solutions' in solutions


def test_datasets():
    datasets = model.datasets()
    assert 'electrostatic' in datasets
    assert 'time-dependent' in datasets
    assert 'parametric sweep' in datasets


def test_plots():
    plots = model.plots()
    assert 'electrostatic field' in plots
    assert 'time-dependent field' in plots
    assert 'evolution' in plots
    assert 'sweep' in plots


def test_exports():
    assert 'field' in model.exports()


def test_groups():
    assert 'functions' in model.groups()


def test_properties():
    assert 'flipx' in model.properties('functions', 'test_function')


def test_rename():
    name = model.name()
    model.rename('test')
    assert model.name() == 'test'
    model.rename(name)
    assert model.name() == name


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


def test_create():
    model.create('functions', 'Interpolation', 'interpolation')
    assert 'interpolation' in model.functions()
    model.create('exports', 'Data', 'vector')
    assert 'vector' in model.exports()


def test_property():
    # Customize newly created features.
    model.property('functions', 'interpolation', 'source', 'file')
    model.property('functions', 'interpolation', 'scaledata', 'off')
    model.property('functions', 'interpolation', 'interp', 'cubicspline')
    model.property('functions', 'interpolation', 'nargs', 1)
    model.property('functions', 'interpolation', 'funcs', ['f', '1'])
    model.property('exports', 'vector', 'expr', ('es.Ex', 'es.Ey', 'es.Ez'))
    model.property('exports', 'vector', 'descr', ('Ex', 'Ey', 'Ez'))
    # Test applying interpolation.
    model.load('table.txt', 'interpolation')
    model.apply_interpolation('electrostatic', 'anode', 'V0', '+U/2 * f(y/l)')
    model.solve('static')
    model.apply_interpolation('electrostatic', 'anode', 'V0', '+U/2')
    model.solve('static')
    # Test conversion to and from 'Boolean'.
    old = model.property('functions', 'test_function', 'flipx')
    model.property('functions', 'test_function', 'flipx', False)
    assert model.property('functions', 'test_function', 'flipx') is False
    model.property('functions', 'test_function', 'flipx', old)
    assert model.property('functions', 'test_function', 'flipx') == old
    # Test conversion to and from 'Double'.
    old = model.property('functions', 'test_function', 'xmin')
    new = -10.0
    model.property('functions', 'test_function', 'xmin', -10)
    assert isclose(model.property('functions', 'test_function', 'xmin'), new)
    model.property('functions', 'test_function', 'xmin', old)
    assert isclose(model.property('functions', 'test_function', 'xmin'), old)
    # Test conversion to and from 'DoubleArray'.
    old = model.property('exports', 'field', 'outersolnumindices')
    new = array([1.0, 2.0, 3.0])
    model.property('exports', 'field', 'outersolnumindices', new)
    assert isclose(model.property('exports', 'field', 'outersolnumindices'),
                   new).all()
    model.property('exports', 'field', 'outersolnumindices', old)
    assert isclose(model.property('exports', 'field', 'outersolnumindices'),
                   old).all()
    # Test conversion to and from 'File'.
    old = model.property('functions', 'test_function', 'filename')
    new = Path('gaussian.tif')
    model.property('functions', 'test_function', 'filename', new)
    assert model.property('functions', 'test_function', 'filename') == new
    model.property('functions', 'test_function', 'filename', old)
    assert model.property('functions', 'test_function', 'filename') == old
    # Test conversion to and from 'Int'.
    old = model.property('functions', 'test_function', 'refreshcount')
    new = 1
    model.property('functions', 'test_function', 'refreshcount', new)
    assert model.property('functions', 'test_function', 'refreshcount') == new
    model.property('functions', 'test_function', 'refreshcount', old)
    assert model.property('functions', 'test_function', 'refreshcount') == old
    # Test conversion to and from 'IntArray'.
    old = model.property('plots', 'evolution', 'solnum')
    new = array([1, 2, 3])
    model.property('plots', 'evolution', 'solnum', new)
    assert (model.property('plots', 'evolution', 'solnum') == new).all()
    model.property('plots', 'evolution', 'solnum', old)
    assert (model.property('plots', 'evolution', 'solnum') == old).all()
    # Test conversion from 'None'.
    none = model.property('functions', 'test_function', 'exportfilename')
    assert none is None
    # Test conversion to and from 'String'.
    old = model.property('functions', 'test_function', 'funcname')
    model.property('functions', 'test_function', 'funcname', 'new')
    assert model.property('functions', 'test_function', 'funcname') == 'new'
    model.property('functions', 'test_function', 'funcname', old)
    assert model.property('functions', 'test_function', 'funcname') == old
    # Test conversion to and from 'StringArray'.
    old = model.property('exports', 'vector', 'descr')
    new = ['x-component', 'y-component', 'z-component']
    model.property('exports', 'vector', 'descr', new)
    assert model.property('exports', 'vector', 'descr') == new
    model.property('exports', 'vector', 'descr', old)
    assert model.property('exports', 'vector', 'descr') == old
    # Test conversion to and from 'StringMatrix'.
    old = model.property('plots', 'evolution', 'plotonsecyaxis')
    new = [['medium 1', 'on', 'ptgr1'], ['medium 2', 'on', 'ptgr2']]
    model.property('plots', 'evolution', 'plotonsecyaxis', new)
    assert model.property('plots', 'evolution', 'plotonsecyaxis') == new
    model.property('plots', 'evolution', 'plotonsecyaxis', old)
    assert model.property('plots', 'evolution', 'plotonsecyaxis') == old


def test_load():
    model.load('gaussian.tif', 'test_function')


def test_remove():
    model.remove('functions', 'interpolation')
    model.remove('exports', 'vector')


def test_build():
    model.build()


def test_mesh():
    model.mesh()


def test_solve():
    model.solve()


def test_evaluate():

    # Test global evaluation of stationary solution.
    expr = '2*es.intWe/U^2'
    unit = 'pF'
    C = model.evaluate(expr, unit)
    assert abs(C - 0.737) < 0.01

    # Test local evaluation of stationary solution.
    expr = ['x', 'y', 'es.normE']
    unit = ['mm', 'mm', 'V/m']
    (x, y, E) = model.evaluate(expr, unit)
    Emax  = E.max()
    index = E.argmax()
    xmax  = x[index]
    ymax  = y[index]
    assert abs(Emax - 814.8) < 0.2
    assert abs(abs(xmax) - 1.037) < 0.001
    assert abs(abs(ymax) - 4.270) < 0.001

    # Test global evaluation of time-dependent solution.
    dset = 'time-dependent'
    expr = '2*ec.intWe/U^2'
    unit = 'pF'
    (indices, values) = model.inner(dset)
    assert values[0] == 0
    assert values[-1] == 1
    Cf = model.evaluate(expr, unit, dset, 'first')
    assert abs(Cf - 0.737) < 0.01
    Cl = model.evaluate(expr, unit, dset, 'last')
    assert abs(Cl - 0.828) < 0.01
    C = model.evaluate(expr, unit, dset)
    assert C[0] == Cf
    assert C[-1] == Cl

    # Test local evaluation of time-dependent solution.
    expr = 'ec.normD'
    unit = 'nC/m^2'
    Df = model.evaluate(expr, unit, dset, 'first')
    assert abs(Df.max() -  7.22) < 0.1
    Dl = model.evaluate(expr, unit, dset, 'last')
    assert abs(Dl.max() - 10.82) < 0.1
    D = model.evaluate(expr, unit, dset)
    assert D[0].max()  == Df.max()
    assert D[-1].max() == Dl.max()

    # Test global evaluation of parameter sweep.
    dset = 'parametric sweep'
    expr = '2*ec.intWe/U^2'
    unit = 'pF'
    (indices, values) = model.outer(dset)
    for (index, value) in zip(indices, values):
        C = model.evaluate(expr, unit, dset, 'first', index)
        if value == 1:
            assert abs(C - 1.319) < 0.01
        elif value == 2:
            assert abs(C - 0.737) < 0.01
        elif value == 3:
            assert abs(C - 0.529) < 0.01
        else:
            raise ValueError(f'Unexpected value {value} for parameter d."')

    # Test local evaluation of parameter sweep.
    for (index, value) in zip(indices, values):
        if value == 2:
            break
    else:
        raise ValueError('Could not find solution for d = 2 mm."')
    expr = 'ec.normD'
    unit = 'nC/m^2'
    Df = model.evaluate(expr, unit, dset, 'first', index)
    assert abs(Df.max() -  7.22) < 0.1
    Dl = model.evaluate(expr, unit, dset, 'last', index)
    assert abs(Dl.max() - 10.82) < 0.1
    D = model.evaluate(expr, unit, dset, outer=index)
    assert D[0].max()  == Df.max()
    assert D[-1].max() == Dl.max()


def test_toggle():
    model.solve('static')
    potential = model.evaluate('V_es')
    assert abs(potential.mean()) < 0.1
    model.toggle('electrostatic', 'cathode')
    model.solve('static')
    potential = model.evaluate('V_es')
    assert abs(potential.mean() - 0.5) < 0.1
    model.toggle('electrostatic', 'cathode', 'on')
    model.solve('static')
    potential = model.evaluate('V_es')
    assert abs(potential.mean()) < 0.1
    model.toggle('electrostatic', 'cathode', 'off')
    model.solve('static')
    potential = model.evaluate('V_es')
    assert abs(potential.mean() - 0.5) < 0.1


def test_export():
    file = Path('field.txt')
    assert not file.exists()
    model.export('field')
    assert file.exists()
    file.unlink()
    file = Path('field2.txt')
    assert not file.exists()
    model.export('field', file)
    assert file.exists()
    file.unlink()
    file = Path('vector.txt')
    assert not file.exists()
    model.property('exports', 'vector', 'exporttype', 'text')
    model.export('vector', file=file)
    assert file.exists()
    file.unlink()
    file = Path('vector.vtu')
    assert not file.exists()
    model.property('exports', 'vector', 'exporttype', 'vtu')
    model.export('vector', file=file)
    assert file.exists()
    file.unlink()


def test_clear():
    model.clear()


def test_reset():
    model.reset()


def test_save():
    model.save(saveas)
    assert saveas.with_suffix('.mph').exists()
    comsol = saveas.with_suffix('.mph').read_text(errors='ignore')
    assert comsol.startswith('PK')
    model.save(saveas.with_suffix('.java'))
    assert saveas.with_suffix('.java').exists()
    java = saveas.with_suffix('.java').read_text(errors='ignore')
    assert 'public static void main' in java
    model.save(saveas.with_suffix('.m'))
    assert saveas.with_suffix('.m').exists()
    matlab = saveas.with_suffix('.m').read_text(errors='ignore')
    assert 'function out = model' in matlab
    model.save(saveas.with_suffix('.vba'))
    assert saveas.with_suffix('.vba').exists()
    vba = saveas.with_suffix('.vba').read_text(errors='ignore')
    assert 'Sub run()' in vba


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
        test_name()
        test_parameters()
        test_functions()
        test_components()
        test_geometries()
        test_selections()
        test_physics()
        test_features()
        test_materials()
        test_meshes()
        test_studies()
        test_solutions()
        test_datasets()
        test_plots()
        test_exports()
        test_groups()
        test_properties()
        test_rename()
        test_parameter()
        test_load()
        test_build()
        test_mesh()
        test_solve()
        test_evaluate()
        test_toggle()
        test_create()
        test_property()
        test_export()
        test_remove()
        test_clear()
        test_reset()
        test_save()
    finally:
        teardown_module()
