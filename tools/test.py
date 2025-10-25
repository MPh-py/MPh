"""
Runs all tests in the intended order.

Each test script (in the `tests` folder) contains a group of tests. These
scripts must be run in separate processes as most of them start and stop the
Java virtual machine, which can only be done once per process. This is why
simply calling pyTest (with `uv run pytest` in the root folder) will not work.

This script here runs each test group in a new subprocess. It also imposes a
logical order: from the tests covering the most basic functionality to the
high-level abstractions.

As opposed to the similar script `coverage.py`, we don't actually run the tests
through pyTest. Rather, we run the scripts directly so that the output is less
verbose. You can further reduce the verbosity by passing `--quiet` as a
command-line argument. This will suppress the log messages produced by MPh as
the tests are running. You may also pass the name of a test group to run only
that particular one. For example, passing "model" will only run the tests
defined in `test_model.py`.
"""

from subprocess import run
from pathlib    import Path
from timeit     import default_timer as now
from argparse   import ArgumentParser
from sys        import exit


# Define order of test groups.
groups = [
    'config', 'discovery',
    'server', 'session', 'standalone', 'client', 'multi',
    'node', 'model', 'exit',
]

# Determine path of project root folder.
here = Path(__file__).parent
root = here.parent

# Parse command-line arguments.
parser = ArgumentParser(
    prog='test.py',
    description='Runs the MPh test suite.',
    add_help=False, allow_abbrev=False,
)
parser.add_argument(
    '--help',
    help='Show this help message.',
    action='help',
)
parser.add_argument(
    '--quiet',
    help='Suppress log output.',
    action='store_true',
)
parser.add_argument(
    '--groups',
    help='List all test groups.',
    action='store_true',
)
parser.add_argument(
    'group',
    help='Run only this group of tests. If not given, run all tests.',
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

# Collect optional arguments to be passed to all test scripts.
options = []
if arguments.quiet:
    options.append('--quiet')

# Run each test group in new process.
for group in groups:
    if groups.index(group) > 0:
        print()
    print(f'Running test group "{group}".')
    t0 = now()
    process = run(
        ['uv', 'run',  '--no-sync', f'test_{group}.py', *options],
        cwd=root/'tests',
    )
    if process.returncode == 0:
        print(f'Passed in {now()-t0:.0f} s.')
    else:
        print(f'Failed after {now()-t0:.0f} s.')
        exit(1)
