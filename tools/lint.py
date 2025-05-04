"""Lints the code for style errors."""

from subprocess import run
from pathlib import Path


root = Path(__file__).parent.parent

run(['ruff', 'check'], cwd=root, check=True)
