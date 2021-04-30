"""Tests the `model` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from models import capacitor
from pathlib import Path
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
    model = capacitor()


def teardown_module():
    client.clear()
    here = Path(__file__).resolve().parent
    files = (here/'model.mph', here/'model2.mph',
             here/'model.java', here/'model.m', here/'model.vba',
             here/'data.txt', here/'data.vtu', here/'image.png')
    for file in files:
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


def test_contains():
    assert 'functions' in model
    assert 'functions/step' in model
    other = client.create('other')
    assert (other/'functions') in model
    assert (other/'functions'/'step') in model
    client.remove(other)


def test_iter():
    assert model/'functions' in list(model)
    assert model/'functions'/'step' not in list(model)


def test_name():
    assert model.name() == 'capacitor'


def test_file():
    assert model.file().name == Path().resolve().name


def test_version():
    assert model.version() == mph.discovery.backend()['name']


def test_functions():
    assert 'step'  in model.functions()


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
    assert 'data'  in model.exports()
    assert 'image' in model.exports()


def test_build():
    model.build()


def test_mesh():
    model.mesh()


def test_solve():
    model.solve()


def test_inner():
    (indices, values) = model.inner('time-dependent')
    assert indices.dtype.kind == 'i'
    assert values.dtype.kind  == 'f'
    assert (indices == list(range(1,102))).all()
    assert values[0] == 0
    assert values[-1] == 1


def test_outer():
    (indices, values) = model.outer('parametric sweep')
    assert indices.dtype.kind == 'i'
    assert values.dtype.kind  == 'f'
    assert (indices == list(range(1,4))).all()
    assert values[0] == 1.0
    assert values[1] == 2.0
    assert values[2] == 3.0


def test_evaluate():
    # Test global evaluation of stationary solution.
    C = model.evaluate('2*es.intWe/U^2', 'pF')
    assert abs(C - 0.74) < 0.01
    # Test field evaluation of stationary solution.
    (x, y, E) = model.evaluate(['x', 'y', 'es.normE'], ['mm', 'mm', 'V/m'])
    (Emax, xmax, ymax) = (E.max(), x[E.argmax()], y[E.argmax()])
    assert abs(Emax - 818) < 5
    assert abs(abs(xmax) - 1.04) < 0.01
    assert abs(abs(ymax) - 4.27) < 0.01
    # Test global evaluation of time-dependent solution.
    (dataset, expression, unit) = ('time-dependent', '2*ec.intWe/U^2', 'pF')
    Cf = model.evaluate(expression, unit, dataset, 'first')
    assert abs(Cf - 0.74) < 0.01
    Cl = model.evaluate(expression, unit, dataset, 'last')
    assert abs(Cl - 0.83) < 0.01
    C = model.evaluate(expression, unit, dataset)
    assert C[0] == Cf
    assert C[-1] == Cl
    # Test field evaluation of time-dependent solution.
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
    C1 = model.evaluate(expression, unit, dataset, 'first', 1)
    assert abs(C1 - 1.32) < 0.01
    C2 = model.evaluate(expression, unit, dataset, 'first', 2)
    assert abs(C2 - 0.74) < 0.01
    C3 = model.evaluate(expression, unit, dataset, 'first', 3)
    assert abs(C3 - 0.53) < 0.01
    # Test field evaluation of parameter sweep.
    (dataset, expression, unit) = ('parametric sweep', 'ec.normD', 'nC/m^2')
    Df = model.evaluate(expression, unit, dataset, 'first', 2)
    assert abs(Df.max() -  7.2) < 0.1
    Dl = model.evaluate(expression, unit, dataset, 'last', 2)
    assert abs(Dl.max() - 10.8) < 0.1
    D = model.evaluate(expression, unit, dataset, outer=2)
    assert D[0].max()  == Df.max()
    assert D[-1].max() == Dl.max()


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
    model.parameter('U', '2')
    assert model.parameter('U') == '2'
    assert model.parameter('U', evaluate=True) == 2
    model.parameter('U', 3)
    assert model.parameter('U') == '3'
    assert model.parameter('U', evaluate=True) == 3
    model.parameter('U', 1+1j)
    assert model.parameter('U') == '(1+1j)'
    assert model.parameter('U', evaluate=True) == 1+1j
    model.parameter('U', value)
    assert model.parameter('U') == value


def test_parameters():
    assert 'U' in model.parameters()
    assert 'U' in model.parameters().keys()
    assert '1[V]' in model.parameters().values()
    assert ('U', '1[V]') in model.parameters().items()


def test_description():
    assert model.description('U') == 'applied voltage'
    model.description('U', 'test')
    assert model.description('U') == 'test'
    model.description('U', 'applied voltage')
    assert model.description('U') == 'applied voltage'


def test_descriptions():
    assert 'U' in model.descriptions()
    assert 'U' in model.descriptions().keys()
    assert 'applied voltage' in model.descriptions().values()
    assert ('U', 'applied voltage') in model.descriptions().items()


def test_property():
    assert model.property('functions/step', 'funcname') == 'step'
    model.property('functions/step', 'funcname', 'renamed')
    assert model.property('functions/step', 'funcname') == 'renamed'
    model.property('functions/step', 'funcname', 'step')
    assert model.property('functions/step', 'funcname') == 'step'
    assert model.property('functions/step', 'from') == 0.0
    model.property('functions/step', 'from', 0.1)
    assert model.property('functions/step', 'from') == 0.1
    model.property('functions/step', 'from', 0.0)
    assert model.property('functions/step', 'from') == 0.0


def test_properties():
    assert 'funcname' in model.properties('functions/step')


def test_create():
    model.create('functions/interpolation', 'Interpolation')
    assert 'interpolation' in model.functions()


def test_remove():
    model.remove('functions/interpolation')
    assert 'interpolation' not in model.functions()


def test_import():
    # Create interpolation function based on external image.
    image = model.create('functions/image', 'Image')
    image.property('funcname', 'im')
    image.property('fununit', '1/m^2')
    image.property('xmin', -5)
    image.property('xmax', +5)
    image.property('ymin', -5)
    image.property('ymax', +5)
    image.property('extrap', 'value')
    # Create interpolation table.
    table = model.create('functions/table', 'Interpolation')
    table.property('funcname', 'f')
    table.property('table', [
        ['+1',   '+2'],
        ['+0.5', '+1'],
        [ '0',    '0'],
        ['-0.5', '-1'],
        ['-1',   '-2'],
    ])
    table.property('interp', 'cubicspline')
    # Import image with file name specified as string and Path.
    here = Path(__file__).resolve().parent
    assert image.property('sourcetype') == 'user'
    model.import_(image, str(here/'gaussian.tif'))
    assert image.property('sourcetype') == 'model'
    image.java.discardData()
    assert image.property('sourcetype') == 'user'
    model.import_(image, here/'gaussian.tif')
    assert image.property('sourcetype') == 'model'
    # Solve with pre-defined boundary condition.
    model.solve('static')
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
    # Remove test fixtures.
    model.remove('functions/image')
    model.remove('functions/table')


def test_export():
    here = Path(__file__).resolve().parent
    assert not (here/'data.txt').exists()
    model.export('data', here/'data.txt')
    assert (here/'data.txt').exists()
    (here/'data.txt').unlink()
    assert not (here/'data.txt').exists()
    model.export('exports/data')
    assert (here/'data.txt').exists()
    (here/'data.txt').unlink()
    assert not (here/'data.txt').exists()
    model.export(model/'exports'/'data')
    assert (here/'data.txt').exists()
    (here/'data.txt').unlink()
    assert not (here/'data.txt').exists()
    model.property('exports/data', 'exporttype', 'text')
    model.export('exports/data', here/'data.txt')
    assert (here/'data.txt').exists()
    (here/'data.txt').unlink()
    assert not (here/'data.vtu').exists()
    model.property('exports/data', 'exporttype', 'vtu')
    model.export('exports/data', here/'data.vtu')
    assert (here/'data.vtu').exists()
    (here/'data.vtu').unlink()
    assert not (here/'image.png').exists()
    model.export('image', here/'image.png')
    assert (here/'image.png').exists()
    (here/'image.png').unlink()
    assert not (here/'image.png').exists()
    model.export()
    assert (here/'data.vtu').exists()
    assert (here/'image.png').exists()
    (here/'data.vtu').unlink()
    (here/'image.png').unlink()
    assert not (here/'data.vtu').exists()
    assert not (here/'image.png').exists()


def test_clear():
    model.clear()


def test_reset():
    model.reset()


def test_save():
    here = Path(__file__).resolve().parent
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
    image = model.create('functions/image', 'Image')
    image.property('funcname', 'im')
    image.property('fununit', '1/m^2')
    image.property('xmin', -5)
    image.property('xmax', +5)
    image.property('ymin', -5)
    image.property('ymax', +5)
    image.property('extrap', 'value')
    model.load('gaussian.tif', 'image')
    model.remove('functions/image')


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
        test_contains()
        test_iter()

        test_name()
        test_file()
        test_version()
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

        test_inner()
        test_outer()
        test_evaluate()

        test_rename()
        test_parameter()
        test_parameters()
        test_description()
        test_descriptions()
        test_property()
        test_properties()
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
