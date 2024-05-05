"""Builds the documentation locally."""

from subprocess import run
from pathlib import Path

root = Path(__file__).resolve().parent.parent
run(['sphinx-build', 'docs', 'build/docs'], cwd=root, check=True)
