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
file   = here/'capacitor.mph'


def setup_module():
    global server
    server = mph.Server(cores=cores)


def teardown_module():
    server.stop()


########################################
# Tests                                #
########################################

def test_server_running():
    assert server.running()


def test_client_connect():
    global client
    client = mph.Client(port=server.port)
    assert not client.models()
    assert client.cores == cores


def test_client_create():
    name = 'test'
    client.create(name)
    assert name in client.names()


def test_client_clear():
    client.clear()
    assert not client.models()


def test_client_load():
    global model
    assert file.is_file()
    model = client.load(file)
    assert model
    assert model.name() in client.names()


def test_model_load():
    model.load('gaussian.tif', 'test_function')


def test_model_build():
    model.build()


def test_model_mesh():
    model.mesh()


def test_model_solve():
    model.solve()


def test_client_remove():
    name = model.name()
    client.remove(model)
    assert name not in client.names()
    message = None
    try:
        model.java.component()
    except Exception as error:
        message = error.getMessage()
    assert 'no_longer_in_the_model' in message


def test_client_disconnect():
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
    if 'log' in arguments or 'debug' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    setup_module()
    try:
        test_server_running()
        test_client_connect()
        test_client_load()
        test_client_create()
        test_client_clear()
        test_client_load()
        test_model_load()
        test_model_build()
        test_model_mesh()
        test_model_solve()
        test_client_remove()
        test_client_disconnect()
    finally:
        teardown_module()
