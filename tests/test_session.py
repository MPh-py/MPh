"""Tests the `session` module in client–server mode."""

import mph

from fixtures import logging_disabled
from fixtures import setup_logging

from pytest import raises


def test_start():
    with logging_disabled(), raises(ValueError):
        mph.option('session', 'invalid')
        mph.start()
    mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.java is not None
    assert client.cores == 1


if __name__ == '__main__':
    setup_logging()
    test_start()
