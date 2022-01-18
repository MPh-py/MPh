"""Tests the `meta` module."""

########################################
# Dependencies                         #
########################################
from mph import meta
from fixtures import setup_logging
import re


########################################
# Tests                                #
########################################

def test_meta():
    fields = ['title', 'synopsis', 'version', 'author', 'copyright', 'license']
    for field in fields:
        assert hasattr(meta, field)
        assert isinstance(getattr(meta, field), str)
    assert meta.title == 'MPh'
    assert meta.synopsis
    assert re.match(r'\d+\.\d+\.\d+', meta.version)
    assert meta.author
    assert meta.copyright
    assert meta.license


########################################
# Main                                 #
########################################

if __name__ == '__main__':
    setup_logging()
    test_meta()
