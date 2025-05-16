"""Builds the documentation locally."""

from subprocess import run
from pathlib    import Path


root = Path(__file__).parent.parent
source = root/'docs'
target = root/'build'/'docs'

process = run(
    ['sphinx-build', '--fail-on-warning', 'docs', 'build/docs'],
    cwd=root
)
if process.returncode:
    raise RuntimeError('Error while rendering documentation.')
