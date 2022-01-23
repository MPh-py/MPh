"""Uploads the coverage report to CodeCov."""

from subprocess import run
from pathlib import Path
from os import environ

token = environ.get('MPh_CodeCov_token', None)
if not token:
    raise RuntimeError('CodeCov upload token not set in environment.')

root = Path(__file__).resolve().parent.parent
run(['codecov', '--file', 'coverage.xml', '--token', token], cwd=root)
