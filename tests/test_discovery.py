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

def test_versions():
    versions = mph.discovery.versions()
    assert bool(versions)


def test_folder():
    folder = mph.discovery.folder()
    assert folder.is_dir()


def test_architecture():
    architecture = mph.discovery.architecture()
    architectures = ('win64', 'glnxa64', 'maci64')
    assert architecture in architectures


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_versions()
    test_folder()
    test_architecture()
