"""Builds the documentation locally."""

from subprocess import run
from pathlib import Path

root = Path(__file__).resolve().parent.parent
process = run(['sphinx-build', 'docs', 'tools/docs'], cwd=root)
if process.returncode:
    raise RuntimeError('Error while rendering documentation.')
