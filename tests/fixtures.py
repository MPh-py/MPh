"""Fixtures used by the test suite."""
__license__ = 'MIT'


import logging
import warnings
from io import StringIO
import sys


class logging_disabled:

    def __enter__(self):
        self.level = logging.getLogger().level
        logging.getLogger().setLevel(100)
        return self

    def __exit__(self, type, value, traceback):
        logging.getLogger().setLevel(self.level)


class warnings_disabled:

    def __enter__(self):
        warnings.simplefilter('ignore')
        return self

    def __exit__(self, type, value, traceback):
        warnings.resetwarnings()


class capture_stdout:

    def __enter__(self):
        self.stdout = sys.stdout
        self.buffer = StringIO()
        sys.stdout = self.buffer
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout

    def text(self):
        return self.buffer.getvalue()
