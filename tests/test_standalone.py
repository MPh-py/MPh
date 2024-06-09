"""Tests the `session` module in stand-alone mode."""

########################################
# Dependencies                         #
########################################
import mph
from fixtures import logging_disabled
from fixtures import setup_logging
from pytest import raises
from platform import system


########################################
# Tests                                #
########################################

def test_start():
    if system() != 'Windows':
        return
    client = mph.start(cores=1)
    assert client.java
    assert client.cores == 1
    assert repr(client) == 'Client(stand-alone)'
    model = client.create('empty')
    assert 'empty' in client.names()
    assert model in client.models()
    (model/'components').create(True)
    client.remove(model)
    assert 'empty' not in client.names()
    assert model not in client.models()
    with logging_disabled():
        contains_text = (
            '(Model node X is removed)'                 # Comsol 6.1 or below
            '|'
            '(object which is no longer in the model)'  # Comsol 6.2+
        )
        with raises(Exception, match=contains_text):
            model.java.component()
        with raises(ValueError):
            client.remove(model)
        with raises(RuntimeError):
            client.connect(2036)
        with raises(RuntimeError):
            client.disconnect()


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    test_start()
