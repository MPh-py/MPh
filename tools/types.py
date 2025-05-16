"""Checks the code for type errors."""

from subprocess import run
from pathlib    import Path


root = Path(__file__).parent.parent

run(['basedpyright'], cwd=root, check=True)
