"""Tests multiple client connections to the same server."""

import mph
from mph import Server

from fixtures import setup_logging

from time import monotonic, sleep


server: Server | None = None

# How long a server gets to shut down. Used where we assert one survived a
# disconnect, since there is no event to await there.
grace = 15

# How long we wait for a server to go away. Polling returns as soon as it has,
# so a generous deadline costs nothing.
patience = 60


def wait_until(predicate, timeout: float = patience):
    """Waits until the predicate holds, failing once the time-out is up."""
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        if predicate():
            return
        sleep(0.25)
    assert predicate()


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
    wait_until(lambda: not server.running())
    assert not server.running()
    server = mph.Server(cores=1, multi=True)
    client.connect(port=server.port)
    assert client.version == server.version
    assert client.cores == server.cores
    assert client.port == server.port
    client.disconnect()
    # The server has to outlive the disconnect. Fail as soon as it stops.
    deadline = monotonic() + grace
    while monotonic() < deadline:
        assert server.running()
        sleep(0.25)
    server.stop()


if __name__ == '__main__':
    setup_logging()
    try:
        test_multi()
    finally:
        teardown_module()
