"""
Runs all tests in the intended order.

Each test script (in the `tests` folder) contains a group of tests.
These scripts must be run in separate processes as most of them start
and stop the Java virtual machine, which can only be done once per
process. This is why simply calling pyTest (with `python -m pytest`
in the root folder) will not work.

This script here runs each test group in a new subprocess. It also
imposes a logical order: from the tests covering the most basic
functionality to the high-level abstractions.

Here, as opposed to the similar script `coverage.py`, we don't actually
run the tests through pyTest. Rather, we run the scripts directly so
that the output is less verbose. Note, however, that pyTest still needs
to be installed as some of the test fixtures require it.

The verbosity can be increased by passing `--log` as a command-line
argument. This will display the log messages produced by MPh as the
tests are running. You can also pass the name of a test group to run
only that one. For example, passing "model" will only run the tests
defined in `test_model.py`.
"""

from subprocess import run
from pathlib    import Path
from timeit     import default_timer as now
from argparse   import ArgumentParser
from sys        import executable as python
from sys        import exit
from os         import environ, pathsep


# Define order of test groups.
groups = ['meta', 'config', 'discovery', 'server', 'session', 'standalone',
          'client', 'multi', 'node', 'model', 'exit']

# Determine path of project root folder.
here = Path(__file__).resolve().parent
root = here.parent

# Run MPh in project folder, not a possibly different installed version.
if 'PYTHONPATH' in environ:
    environ['PYTHONPATH'] = str(root) + pathsep + environ['PYTHONPATH']
else:
    environ['PYTHONPATH'] = str(root)

# Parse command-line arguments.
parser = ArgumentParser(prog='test.py',
                        description='Runs the MPh test suite.',
                        add_help=False,
                        allow_abbrev=False)
parser.add_argument('--help',
                    help='Show this help message.',
                    action='help')
parser.add_argument('--log',
                    help='Display log output.',
                    action='store_true')
parser.add_argument('--groups',
                    help='List all test groups.',
                    action='store_true')
parser.add_argument('group',
                    help='Run only this group of tests.',
                    nargs='?')
arguments = parser.parse_args()
if arguments.groups:
    for group in groups:
        print(group)
    exit()
if arguments.group:
    group = arguments.group
    if group.startswith('test_'):
        group = group[5:]
    if group.endswith('.py'):
        group = group[:-3]
    groups = [group]
options = []
if arguments.log:
    options.append('--log')

# Run each test group in new process.
for group in groups:
    if groups.index(group) > 0:
        print()
    print(f'Running test group "{group}".')
    t0 = now()
    process = run([python, f'test_{group}.py'] + options, cwd=root/'tests')
    if process.returncode == 0:
        print(f'Passed in {now()-t0:.0f} s.')
    else:
        print(f'Failed after {now()-t0:.0f} s.')
        exit(1)
