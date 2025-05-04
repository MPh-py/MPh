"""Packages the library as a distribution wheel."""

from subprocess import run
from pathlib import Path


root = Path(__file__).parent.parent

process = run(['uv', 'build', '--wheel', '--out-dir', 'build/wheel'], cwd=root)
if process.returncode:
    raise RuntimeError('Error while building wheel.')
