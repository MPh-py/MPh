"""Lints the code for style errors."""

from subprocess import run
from pathlib import Path

root = Path(__file__).resolve().parent.parent
run(['flake8'], cwd=root, check=True)
