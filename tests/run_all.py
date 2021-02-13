"""Runs all tests in the intended order, while logging to the console."""
__license__ = 'MIT'

from subprocess import run
from pathlib import Path
from platform import system
from sys import argv

here = Path(__file__).parent
arguments = argv[1:]
if 'log' not in arguments:
    arguments.append('log')

for test in ('discovery', 'client', 'model', 'server', 'remote', 'processes'):
    print(f'test_{test}')
    if system() in ('Linux', 'Darwin'):
        python = 'python3'
    else:
        python = 'python'
    process = run([python, f'test_{test}.py'] + arguments, cwd=here)
    if process.returncode != 0:
        break
    print()
