"""Tests discovering back-end installations."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent
import mph
import logging
from sys import argv


########################################
# Tests                                #
########################################

def test_parse():
    version = 'COMSOL Multiphysics 5.5.0.359'
    (name, major, minor, patch, build) = mph.discovery.parse(version)
    assert name == '5.5'
    assert major == 5
    assert minor == 5
    assert patch == 0
    assert build == 359


def test_backend():
    backends = mph.discovery.backend()
    assert bool(backends)


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments or 'debug' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_parse()
    test_backend()
