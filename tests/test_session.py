"""Tests the `session` and `client` modules."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from pathlib import Path
from sys import argv
import logging


########################################
# Fixtures                             #
########################################
client = None
cores  = 1
model  = None
demo   = Path(__file__).resolve().parent.parent/'demos'/'capacitor.mph'


def setup_module():
    pass


def teardown_module():
    pass


########################################
# Tests                                #
########################################

def test_init():
    global client
    client = mph.start(cores=cores)
    assert client.java is not None
    assert client.cores == cores


def test_repr():
    if client.port:
        assert repr(client) == f'Client(port={client.port})'
    else:
        assert repr(client) == 'Client(stand-alone)'


def test_load():
    global model
    assert demo.is_file()
    model = client.load(demo)
    assert model


def test_caching():
    assert not client.caching()
    copy = client.load(demo)
    assert model != copy
    client.remove(copy)
    client.caching(True)
    assert client.caching()
    copy = client.load(demo)
    assert model == copy
    client.caching(False)
    assert not client.caching()


def test_create():
    name = 'test'
    client.create(name)
    assert name in client.names()


def test_models():
    pass


def test_names():
    assert model.name() in client.names()


def test_files():
    assert demo in client.files()


def test_contains():
    assert model in client
    assert 'capacitor' in client
    assert 'test' in client


def test_iter():
    models = list(client)
    assert model in models


def test_truediv():
    assert client/'capacitor' == model


def test_remove():
    name = model.name()
    assert name in client.names()
    client.remove(model)
    assert name not in client.names()
    message = ''
    try:
        model.java.component()
    except Exception as error:
        message = error.getMessage()
    if client.port:
        assert 'no_longer_in_the_model' in message
    else:
        assert 'is_removed' in message


def test_clear():
    client.clear()
    assert not client.models()


def test_disconnect():
    if client.port:
        client.disconnect()
        try:
            client.models()
            connected = True
        except Exception:
            connected = False
        assert not connected


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
        test_repr()
        test_load()
        test_caching()
        test_create()
        test_models()
        test_names()
        test_files()
        test_contains()
        test_iter()
        test_truediv()
        test_remove()
        test_clear()
        test_disconnect()
    finally:
        teardown_module()
