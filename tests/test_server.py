"""Tests the `server` module."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import logging_disabled
from fixtures import setup_logging


########################################
# Fixtures                             #
########################################
server = None


def teardown_module():
    if server and server.running():
        server.stop()


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
    setup_logging()
    try:
        test_init()
        test_repr()
        test_running()
        test_stop()
    finally:
        teardown_module()
