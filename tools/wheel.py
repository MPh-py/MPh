"""Builds the packaged wheel."""

from subprocess import run
from pathlib import Path
from shutil import rmtree

root = Path(__file__).resolve().parent.parent
run(['flit', 'build', '--format', 'wheel'], cwd=root, check=True)

source = root/'dist'
target = root/'build'/'wheel'
if target.exists():
    rmtree(target)
target.parent.mkdir(exist_ok=True, parents=True)
source.rename(target)
