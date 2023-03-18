"""Tests the `server` module."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import logging_disabled
from fixtures import setup_logging
from fixtures import capture_stderr
from pytest import raises


########################################
# Fixtures                             #
########################################
server = None


def teardown_module():
    if server and server.running():
        server.stop()


########################################
# Tests                                #
########################################

def test_init():
    global server
    with raises(RuntimeError), capture_stderr():
        server = mph.Server(arguments=['-version'])
    server = mph.Server(cores=1, port=2035)
    assert server.port == 2035


def test_repr():
    assert repr(server) == f'Server(port={server.port})'


def test_running():
    assert server.running()


def test_stop():
    server.stop()
    assert not server.running()
    with logging_disabled():
        server.stop()


def test_parse_port():
    english = ('COMSOL Multiphysics server 5.6 (Build: 401) started '
               'listening on port 2036')
    german  = ('COMSOL Multiphysics server 5.4 (Build-Version: 388) '
               'startete Abhören an Port 2036')
    chinese = ('COMSOL Multiphysics server 5.6 (开发版本: 341) '
               '开始在端口 2036 上监听')
    assert mph.server.parse_port(english) == 2036
    assert mph.server.parse_port(german)  == 2036
    assert mph.server.parse_port(chinese) == 2036
    english = ('COMSOL Multiphysics server 5.6 (Build: 401) started '
               'listening on port 12345')
    german  = ('COMSOL Multiphysics server 5.4 (Build-Version: 388) '
               'startete Abhören an Port 12345')
    chinese = ('COMSOL Multiphysics server 5.6 (开发版本: 341) '
               '开始在端口 12345 上监听')
    assert mph.server.parse_port(english) == 12345
    assert mph.server.parse_port(german)  == 12345
    assert mph.server.parse_port(chinese) == 12345


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    try:
        test_init()
        test_repr()
        test_running()
        test_stop()
        test_parse_port()
    finally:
        teardown_module()
