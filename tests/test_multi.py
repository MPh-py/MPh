"""Tests multiple client connections to the same server."""

########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from sys import argv
from time import sleep
from pytest import raises
import logging


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

def test_multi():
    global server
    with raises(ValueError):
        server = mph.Server(multi='invalid')
    server = mph.Server(cores=1, multi=False)
    assert server.running()
    assert server.port
    client = mph.Client(port=server.port)
    assert not client.standalone
    assert client.version == server.version
    assert client.cores == server.cores
    assert client.port == server.port
    client.disconnect()
    sleep(3)
    assert not server.running()
    server = mph.Server(cores=1, multi=True)
    client.connect(port=server.port)
    assert client.version == server.version
    assert client.cores == server.cores
    assert client.port == server.port
    client.disconnect()
    sleep(3)
    assert server.running()
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
        test_multi()
    finally:
        teardown_module()
