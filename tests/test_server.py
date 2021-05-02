"""Tests the `server` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
import logging
from sys import argv


########################################
# Fixtures                             #
########################################
server = None


def teardown_module():
    if server and server.running():
        try:
            server.stop()
        except Exception:
            pass


########################################
# Tests                                #
########################################

def test_init():
    global server
    server = mph.Server(cores=1, port=2035)
    assert server.port == 2035


def test_repr():
    assert repr(server) == f'Server(port={server.port})'


def test_running():
    assert server.running()


def test_stop():
    server.stop()
    assert not server.running()
    with logging_disabled():
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

    try:
        test_init()
        test_repr()
        test_running()
        test_stop()
    finally:
        teardown_module()
