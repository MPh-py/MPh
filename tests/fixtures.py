"""Fixtures used by the test suite."""

import logging
import warnings
import tempfile
import io
import sys
from pathlib import Path


def temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix='MPh_tests_'))


class logging_disabled:
    """Suppresses log messages issued in this context."""

    def __enter__(self):
        self.level = logging.getLogger().level
        logging.getLogger().setLevel(100)
        return self

    def __exit__(self, type, value, traceback):
        logging.getLogger().setLevel(self.level)


class warnings_disabled:
    """Suppresses warnings raised in this context."""

    def __enter__(self):
        warnings.simplefilter('ignore')
        return self

    def __exit__(self, type, value, traceback):
        warnings.resetwarnings()


class capture_stdout:
    """Captures text written to `sys.stdout` in this context."""

    def __enter__(self):
        self.stdout = sys.stdout
        self.buffer = io.StringIO()
        sys.stdout  = self.buffer
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self.stdout

    def text(self):
        return self.buffer.getvalue()


class capture_stderr:
    """Captures text written to `sys.stdout` in this context."""

    def __enter__(self):
        self.stderr = sys.stderr
        self.buffer = io.StringIO()
        sys.stderr  = self.buffer
        return self

    def __exit__(self, type, value, traceback):
        sys.stderr = self.stderr

    def text(self):
        return self.buffer.getvalue()


original_records = logging.getLogRecordFactory()


def timed_records(*args, **kwargs):
    """Adds a (relative) `timestamp` to the log record attributes."""
    record = original_records(*args, **kwargs)
    (minutes, seconds) = divmod(record.relativeCreated/1000, 60)
    record.timestamp = f'{minutes:02.0f}:{seconds:06.3f}'
    return record


def setup_logging():
    """Sets up logging to console unless `--quiet` passed on command line."""
    if '--quiet' in sys.argv[1:]:
        return
    logging.setLogRecordFactory(timed_records)
    logging.basicConfig(
        level  = logging.DEBUG,
        format = '[%(timestamp)s] %(message)s',
    )
