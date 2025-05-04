"""Publishes the package on PyPI."""

from subprocess import run
from pathlib import Path


root = Path(__file__).parent.parent

process = run(['uv', 'publish', 'build/wheel/*.whl'], cwd=root)
if process.returncode:
    raise RuntimeError('Error while publishing to PyPI.')
