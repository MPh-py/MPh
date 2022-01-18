"""Tests the `config` module."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import logging_disabled
from fixtures import setup_logging
from pytest import raises
from pathlib import Path


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
        with raises(LookupError):
            mph.option('non-existing')
        with raises(LookupError):
            mph.option('non-existing', 'assigned value')


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
    setup_logging()
    test_option()
    test_location()
    test_save()
    test_load()
