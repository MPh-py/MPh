"""Publishes the package on PyPI."""

from subprocess import run
from pathlib import Path

root = Path(__file__).resolve().parent.parent
process = run(['flit', 'publish', '--format', 'wheel'], cwd=root)
if process.returncode:
    raise RuntimeError('Error while publishing on PyPI.')
