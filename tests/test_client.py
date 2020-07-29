"""Tests a stand-alone client session."""
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
client = None
model  = None
here   = Path(__file__).parent
file   = here / 'capacitor.mph'


def setup_module():
    pass


def teardown_module():
    pass


########################################
# Tests                                #
########################################

def test_start():
    global client
    client = mph.Client(cores=1)
    assert client.java is not None


def test_cores():
    assert client.cores == 1


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
    assert 'is_removed' in message


def test_clear():
    client.clear()
    assert not client.models()


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
        test_start()
        test_cores()
        test_load()
        test_create()
        test_list()
        test_remove()
        test_clear()
    finally:
        teardown_module()
