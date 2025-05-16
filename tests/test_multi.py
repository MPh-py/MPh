"""Tests multiple client connections to the same server."""

import mph
from mph import Server

from fixtures import setup_logging

from time import sleep


server: Server


def teardown_module():
    if server and server.running():
        try:
            server.stop()
        except Exception:
            pass


def test_multi():
    global server
    server = mph.Server(cores=1, multi=False)
    assert server.running()
    assert server.port
    client = mph.Client(port=server.port)
    assert not client.standalone
    assert client.version == server.version
    assert client.cores == server.cores
    assert client.port == server.port
    client.disconnect()
    sleep(15)
    assert not server.running()
    server = mph.Server(cores=1, multi=True)
    client.connect(port=server.port)
    assert client.version == server.version
    assert client.cores == server.cores
    assert client.port == server.port
    client.disconnect()
    sleep(15)
    assert server.running()
    server.stop()


if __name__ == '__main__':
    setup_logging()
    try:
        test_multi()
    finally:
        teardown_module()
