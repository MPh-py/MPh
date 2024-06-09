"""Builds the documentation locally."""

from subprocess import run
from pathlib import Path
from sys import argv as arguments
from shutil import rmtree


root = Path(__file__).resolve().parent.parent
source = root/'docs'
target = root/'build'/'docs'

# Build from a clean slate if command-line argument "clean" is passed.
# For certain changes, such as to the custom style sheet, Sphinx would
# otherwise use the cached files from the last build.
if len(arguments) > 1 and arguments[1] == "clean":
    if target.exists():
        rmtree(target)

run(['sphinx-build', 'docs', 'build/docs'], cwd=root, check=True)
