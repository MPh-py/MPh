"""Runs all tests in the intended order."""
__license__ = 'MIT'


from subprocess import run
from pathlib import Path
from sys import argv


here = Path(__file__).parent
arguments = argv[1:]

for test in ('backend', 'client', 'model', 'server', 'remote'):
    result = run(['python', f'test_{test}.py'] + arguments, cwd=here)
    if result.returncode:
        break
