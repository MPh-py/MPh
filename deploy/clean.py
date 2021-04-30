"""Deletes cache and build artifacts."""
__license__ = 'MIT'

from pathlib import Path
from shutil import rmtree

root = Path(__file__).resolve().parent.parent

for folder in root.rglob('__pycache__'):
    rmtree(folder, ignore_errors=True)

for folder in root.rglob('.pytest_cache'):
    rmtree(folder)

for folder in ('docs', 'dist', 'coverage'):
    rmtree(root/'deploy'/folder, ignore_errors=True)
