"""Lints the code for style errors."""

from subprocess import run
from pathlib    import Path


root = Path(__file__).parent.parent

run(
    [
        'uv', 'run', '--no-sync',
        'ruff', 'check',
    ],
    cwd=root, check=True,
)
