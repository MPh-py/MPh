"""Tests the node class."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from mph.node import Node
from sys import argv
from pathlib import Path
import logging


########################################
# Fixtures                             #
########################################
client = None
model  = None
here   = Path(__file__).parent
file   = here/'capacitor.mph'
saveas = here/'temp'


def setup_module():
    global client, model
    client = mph.start()
    model = client.load(file)


def teardown_module():
    pass


########################################
# Tests                                #
########################################

def test_init():
    node = Node(model, 'functions')
    assert node.model
    assert node.alias
    assert node.groups


def test_str():
    assert str(Node(model, 'functions/step')) == '/functions/step'


def test_repr():
    assert repr(Node(model, 'functions')) == 'Node(//capacitor/functions)'


def test_eq():
    assert Node(model, 'function') == Node(model, 'functions')


def test_truediv():
    assert Node(model, 'functions')/'step' == Node(model, 'functions/step')


def test_java():
    assert Node(model, 'functions').java
    assert Node(model, 'functions/step').java


def test_name():
    assert Node(model, 'functions').name() == 'functions'
    assert Node(model, 'functions/step').name() == 'step'


def test_tag():
    assert Node(model, 'functions/step').tag() == 'step1'


def test_parent():
    assert Node(model, 'functions/step').parent() == Node(model, 'functions')


def test_children():
    assert Node(model, 'functions/step') in Node(model, 'functions').children()


def test_is_root():
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


def test_properties():
    assert 'funcname' in Node(model, 'functions/step').properties()


def test_property():
    node = Node(model, 'functions/step')
    assert node.property('funcname') == 'step'
    node.property('funcname', 'renamed')
    assert node.property('funcname') == 'renamed'
    node.property('funcname', 'step')
    assert node.property('funcname') == 'step'
    assert node.property('from') == 0.0
    node.property('from', 0.1)
    assert node.property('from') == 0.1
    node.property('from', 0.0)
    assert node.property('from') == 0.0


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
        test_init()
        test_str()
        test_repr()
        test_eq()
        test_truediv()
        test_java()
        test_name()
        test_tag()
        test_parent()
        test_children()
        test_is_root()
        test_is_group()
        test_exists()
        test_rename()
        test_properties()
        test_property()
        test_toggle()
        test_run()
        test_create()
        test_remove()
    finally:
        teardown_module()
