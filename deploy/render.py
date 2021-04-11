"""Renders the documentation."""
__license__ = 'MIT'

from subprocess import run
from pathlib import Path

root = Path(__file__).resolve().parent.parent
process = run(['sphinx-build', 'docs', 'deploy/docs'], cwd=root)
if process.returncode:
    raise RuntimeError('Error while rendering documentation.')
