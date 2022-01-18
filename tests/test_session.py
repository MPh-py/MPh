"""Tests the `session` module in client–server mode."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import logging_disabled
from fixtures import setup_logging
from pytest import raises


########################################
# Tests                                #
########################################

def test_start():
    with logging_disabled():
        with raises(ValueError):
            mph.option('session', 'invalid')
            mph.start()
    mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.java is not None
    assert client.cores == 1


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    test_start()
