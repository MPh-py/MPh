"""Deletes cache and build artifacts."""
__license__ = 'MIT'

from pathlib import Path
from shutil import rmtree

root = Path(__file__).absolute().parent.parent

for folder in root.rglob('__pycache__'):
    rmtree(folder)

for folder in root.rglob('.pytest_cache'):
    rmtree(folder)

for folder in (root/'deploy'/'dist', root/'deploy'/'docs'):
    rmtree(folder, ignore_errors=True)
