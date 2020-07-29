"""Builds documentation and installation package."""
__license__ = 'MIT'


from subprocess import run
from pathlib import Path


main = Path(__file__).absolute().parent.parent

process = run('sphinx-build . rendered', cwd=main/'docs')
if process.returncode:
    raise RuntimeError('Error while building documentation.')

process = run('flit build --format wheel', cwd=main)
if process.returncode:
    raise RuntimeError('Error while building wheel.')
