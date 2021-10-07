"""Tests the `session` module in stand-alone mode."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
from platform import system
from sys import argv
import logging


########################################
# Tests                                #
########################################

def test_start():
    if system() != 'Windows':
        return
    client = mph.start(cores=1)
    assert client.java


def test_cores():
    client = mph.start()
    assert client.cores == 1


def test_repr():
    client = mph.start()
    assert repr(client) == 'Client(stand-alone)'


def test_remove():
    if system() != 'Windows':
        return
    client = mph.start()
    model = client.create('empty')
    assert 'empty' in client.names()
    assert model in client.models()
    (model/'components').create(True)
    client.remove(model)
    assert 'empty' not in client.names()
    assert model not in client.models()
    message = ''
    try:
        model.java.component()
        assert False
    except Exception as error:
        message = error.getMessage()
    assert 'is_removed' in message
    with logging_disabled():
        try:
            client.remove(model)
            assert False
        except ValueError:
            pass


def test_connect():
    if system() != 'Windows':
        return
    client = mph.start()
    with logging_disabled():
        try:
            client.connect(2036)
            assert False
        except RuntimeError:
            pass


def test_disconnect():
    if system() != 'Windows':
        return
    client = mph.start()
    with logging_disabled():
        try:
            client.disconnect()
            assert False
        except RuntimeError:
            pass


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

    test_start()
    test_cores()
    test_repr()
    test_remove()
    test_connect()
    test_disconnect()
