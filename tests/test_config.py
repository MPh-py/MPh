"""Tests the `config` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from sys import argv
import logging


########################################
# Tests                                #
########################################

def test_option():
    assert 'session' in mph.option()
    assert 'platform-dependent' in mph.option().values()
    assert mph.option('session') == 'platform-dependent'
    mph.option('session', 'something else')
    assert mph.option('session') == 'something else'
    mph.option('session', 'platform-dependent')


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

    test_option()
