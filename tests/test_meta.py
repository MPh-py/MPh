"""Tests the `meta` module."""

import parent # noqa F401
from mph import meta
import re


def test_meta():
    fields = ['title', 'synopsis', 'version', 'date', 'author', 'copyright',
              'license']
    for field in fields:
        assert hasattr(meta, field)
        assert isinstance(getattr(meta, field), str)
    assert meta.title == 'MPh'
    assert meta.synopsis
    assert re.match(r'\d+\.\d+\.\d+', meta.version)
    assert re.match(r'\d\d\d\d–\d\d–\d\d', meta.date)
    assert meta.author
    assert meta.copyright
    assert meta.license
