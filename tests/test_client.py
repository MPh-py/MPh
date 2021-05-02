"""Tests the `client` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
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

def test_init():
    global client
    if mph.option('session') == 'platform-dependent':
        mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.java is not None
    assert client.cores == 1
    with logging_disabled():
        try:
            mph.start()
        except NotImplementedError:
            pass
        try:
            mph.Client()
        except NotImplementedError:
            pass


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
    if client.port:
        assert repr(client) == f'Client(port={client.port})'
    else:
        assert repr(client) == 'Client(stand-alone)'


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
        try:
            client/'non-existing'
        except ValueError:
            pass
        try:
            client/model
        except TypeError:
            pass
        try:
            client/False
        except TypeError:
            pass


def test_models():
    assert model in client.models()


def test_names():
    assert model.name() in client.names()


def test_files():
    assert demo in client.files()


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
        try:
            client.caching('anything else')
        except ValueError:
            pass


def test_remove():
    name = model.name()
    assert name in client.names()
    client.remove(model)
    assert name not in client.names()
    assert 'empty' in client.names()
    client.remove('empty')
    assert 'empty' not in client.names()
    message = ''
    try:
        model.java.component()
    except Exception as error:
        message = error.getMessage()
    assert 'no_longer_in_the_model' in message
    with logging_disabled():
        try:
            client.remove(model)
        except ValueError:
            pass
        try:
            client.remove('non-existing')
        except ValueError:
            pass
        try:
            client.remove(True)
        except TypeError:
            pass


def test_clear():
    client.clear()
    assert not client.models()


def test_disconnect():
    client.disconnect()
    assert client.host is None
    assert client.port is None
    with logging_disabled():
        try:
            client.models()
        except Exception:
            pass


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

    test_init()
    test_load()
    test_create()
    test_repr()
    test_contains()
    test_iter()
    test_truediv()
    test_models()
    test_names()
    test_files()
    test_caching()
    test_remove()
    test_clear()
    test_disconnect()
