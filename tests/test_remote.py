"""Tests a remote session: client connected to a server."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent
import mph
import logging
from sys import argv
from pathlib import Path


########################################
# Fixtures                             #
########################################
server = None
client = None
cores  = 1
model  = None
here   = Path(__file__).parent
file   = here / 'capacitor.mph'


def setup_module():
    global server
    server = mph.Server(cores=cores)


def teardown_module():
    server.stop()


########################################
# Tests                                #
########################################

def test_started():
    assert server.running()


def test_connect():
    global client
    client = mph.Client(port=server.port)
    assert not client.models()


def test_cores():
    assert client.cores == cores


def test_load():
    global model
    assert file.is_file()
    model = client.load(file)
    assert model


def test_create():
    name = 'test'
    client.create(name)
    assert name in client.names()


def test_list():
    assert model.name() in client.names()


def test_remove():
    name = model.name()
    client.remove(model)
    assert name not in client.names()
    message = None
    try:
        model.java.component()
    except Exception as error:
        message = error.getMessage()
    assert 'no_longer_in_the_model' in message


def test_clear():
    client.clear()
    assert not client.models()


def test_disconnect():
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
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    setup_module()
    try:
        test_started()
        test_connect()
        test_cores()
        test_load()
        test_create()
        test_list()
        test_remove()
        test_clear()
        test_disconnect()
    finally:
        teardown_module()
