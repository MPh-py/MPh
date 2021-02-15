"""Builds documentation and installation package."""
__license__ = 'MIT'

from subprocess import run
from pathlib import Path
from shutil import rmtree

root = Path(__file__).absolute().parent.parent

process = run('sphinx-build docs deploy/docs', cwd=root, shell=True)
if process.returncode:
    raise RuntimeError('Error while building documentation.')

process = run('flit build --format wheel', cwd=root, shell=True)
if process.returncode:
    raise RuntimeError('Error while building wheel.')
source = root/'dist'
target = root/'deploy'/'dist'
if target.exists():
    rmtree(target)
source.rename(target)
