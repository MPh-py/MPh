"""Tests the `config` module."""

import mph

from fixtures import temp_dir
from fixtures import logging_disabled
from fixtures import setup_logging
from pytest   import raises

from pathlib import Path
from logging import getLogger


tmpdir: Path


def setup_module():
    global tmpdir
    tmpdir = temp_dir()
    log = getLogger(__name__)
    log.debug(f'Temporary folder is "{tmpdir}".')


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
    file = tmpdir/'MPh.ini'
    mph.config.save(file)
    assert file.exists()


def test_load():
    defaults = mph.option().copy()
    file = tmpdir/'defaults.ini'
    mph.config.save(file)
    for (key, value) in defaults.items():
        if isinstance(value, bool):
            mph.option(key, not value)
        elif isinstance(value, (int, float)):
            mph.option(key, value - 1)
        else:
            mph.option(key, value + ' (modified)')
    for (key, value) in defaults.items():
        assert mph.option(key) != value
    mph.config.load(file)
    for (key, value) in defaults.items():
        assert mph.option(key) == value


if __name__ == '__main__':
    setup_logging()
    setup_module()
    test_option()
    test_location()
    test_save()
    test_load()
