"""Tests the `client` module in client–server mode."""

########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
from pytest import raises
from pathlib import Path
from sys import argv
import logging


########################################
# Fixtures                             #
########################################
client = None
model  = None
demo   = Path(__file__).resolve().parent.parent/'demos'/'capacitor.mph'


########################################
# Tests                                #
########################################

# The test are mostly in source-code order of the Client class. Except
# that we load a model and create another one early on, just so we have
# something to work with. And connect() is already called from __init__(),
# which is why disconnect() comes before connect(), which actually tests
# reconnecting the client.

def test_init():
    global client
    mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.version
    assert client.port
    assert client.host == 'localhost'
    assert client.java
    assert not client.standalone
    with logging_disabled():
        with raises(NotImplementedError):
            mph.Client()


def test_load():
    global model
    assert demo.is_file()
    model = client.load(demo)
    assert model


def test_create():
    name = 'empty'
    client.create(name)
    assert name in client.names()
    client.create()
    assert 'Untitled' in client.names()


def test_repr():
    assert repr(client) == f'Client(host=localhost, port={client.port})'


def test_contains():
    assert model in client
    assert 'capacitor' in client
    assert 'empty' in client
    assert 'non-existing' not in client


def test_iter():
    models = list(client)
    assert model in models


def test_truediv():
    assert client/'capacitor' == model
    with logging_disabled():
        with raises(ValueError):
            client/'non-existing'
        with raises(TypeError):
            client/model
        with raises(TypeError):
            client/False


def test_cores():
    assert client.cores == 1


def test_models():
    assert model in client.models()


def test_names():
    assert model.name() in client.names()


def test_files():
    assert demo in client.files()


def test_modules():
    for key in mph.client.modules.keys():
        assert client.java.hasProduct(key) in (True, False)
    for value in mph.client.modules.values():
        assert value in mph.model.modules.values()
    assert 'Comsol core' in client.modules()
    mph.client.modules['invalid'] = 'invalid'
    client.modules()
    del mph.client.modules['invalid']


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
    with logging_disabled():
        with raises(ValueError):
            client.caching('anything else')


def test_remove():
    name = model.name()
    assert name in client.names()
    client.remove(model)
    assert name not in client.names()
    assert 'empty' in client.names()
    client.remove('empty')
    assert 'empty' not in client.names()
    with logging_disabled():
        with raises(Exception, match='is no longer in the model'):
            model.java.component()
        with raises(ValueError):
            client.remove(model)
        with raises(ValueError):
            client.remove('non-existing')
        with raises(TypeError):
            client.remove(True)


def test_clear():
    client.clear()
    assert not client.models()


def test_disconnect():
    client.disconnect()
    assert client.host is None
    assert client.port is None
    assert repr(client) == 'Client(disconnected)'
    with logging_disabled():
        with raises(Exception):
            client.models()
        with raises(RuntimeError):
            client.disconnect()


def test_connect():
    server = mph.Server(cores=1)
    client.connect(server.port)
    assert client.port == server.port
    assert client.cores == 1
    with logging_disabled():
        with raises(RuntimeError):
            client.connect(server.port)
    client.disconnect()
    server.stop()


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG if 'debug' in arguments else logging.INFO,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_init()
    test_load()
    test_create()
    test_repr()
    test_contains()
    test_iter()
    test_truediv()
    test_cores()
    test_models()
    test_names()
    test_files()
    test_caching()
    test_remove()
    test_clear()
    test_disconnect()
    test_connect()
