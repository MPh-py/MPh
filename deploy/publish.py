"""Publishes the package on PyPI."""
__license__ = 'MIT'


from subprocess import run
from pathlib import Path


main = Path(__file__).absolute().parent.parent
process = run('flit publish --format wheel', cwd=main)
if process.returncode:
    raise RuntimeError('Error while publishing to PyPI.')
