"""
Runs all tests in the intended order.

This script does not use pyTest, but runs the test scripts as is,
in a subprocess. We impose the intended order, from the most basic
functionality to the high-level abstractions.

Pass 'log' as a command-line argument to have the scripts print log
messages to the console while the tests are running. Pass 'debug' to
increase the verbosity of the log.
"""

from subprocess import run
from pathlib    import Path
from timeit     import default_timer as now
import sys

tests = ['config', 'discovery', 'server', 'session', 'standalone',
         'client', 'node', 'model', 'processes']

folder = Path(__file__).parent.parent / 'tests'
python = sys.executable
arguments = sys.argv[1:]
for test in tests:
    print(f'test_{test}')
    t0 = now()
    process = run([python, f'test_{test}.py'] + arguments, cwd=folder)
    if process.returncode == 0:
        print(f'Passed in {now()-t0:.0f} s.')
    else:
        print(f'Failed after {now()-t0:.0f} s.')
    print()
