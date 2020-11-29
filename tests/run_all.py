"""Runs all tests in the intended order, while logging to the console."""
__license__ = 'MIT'


from subprocess import run
from pathlib import Path
from sys import argv


here = Path(__file__).parent
arguments = argv[1:]
if 'log' not in arguments:
    arguments.append('log')

for test in ('backend', 'client', 'model', 'server', 'remote'):
    print(f'test_{test}')
    process = run(['python', f'test_{test}.py'] + arguments, cwd=here)
    if process.returncode != 0:
        break
    print()
