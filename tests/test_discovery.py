"""Tests the `discovery` module."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import setup_logging


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
    backend = mph.discovery.backend()
    assert backend['name']
    assert backend['root']
    assert backend['jvm']
    assert backend['server']


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    test_parse()
    test_backend()
