"""Tests the `session` module in client–server mode."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
from sys import argv
import logging


########################################
# Tests                                #
########################################

def test_start():
    with logging_disabled():
        try:
            mph.option('session', 'invalid')
            mph.start()
        except ValueError:
            pass
    mph.option('session', 'client-server')
    client = mph.start(cores=1)
    assert client.java is not None
    assert client.cores == 1
    with logging_disabled():
        try:
            mph.start()
        except NotImplementedError:
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
