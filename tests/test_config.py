"""Tests the `config` module."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
import mph
from fixtures import logging_disabled
from pathlib import Path
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
    with logging_disabled():
        try:
            mph.option('non-existing')
        except LookupError:
            pass
        try:
            mph.option('non-existing', 'assigned value')
        except LookupError:
            pass


def test_location():
    assert mph.config.location().name == 'MPh'


def test_save():
    file = Path(__file__).parent/'MPh.ini'
    mph.config.save(file)
    assert file.exists()


def test_load():
    options = mph.option().copy()
    for (key, value) in options.items():
        if isinstance(value, bool):
            mph.option(key, not value)
        elif isinstance(value, (int, float)):
            mph.option(key, value - 1)
        else:
            mph.option(key, value + '(modified)')
    for (key, value) in options.items():
        assert mph.option(key) != value
    file = Path(__file__).parent/'MPh.ini'
    assert file.exists()
    mph.config.load(file)
    for (key, value) in options.items():
        assert mph.option(key) == value
    file.unlink()
    assert not file.exists()


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
    test_location()
    test_save()
    test_load()
