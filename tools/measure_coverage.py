"""
Measures code coverage by test suite.

This script essentially does the same as `run_tests.py`, but runs each test
group through pyTest with code-coverage reporting turned on. We thus generate
the code-coverage report incrementally and render it as an HTML page for easy
inspection in the `build/coverage` folder.
"""

from subprocess import run
from pathlib    import Path


# Define order of test groups.
groups = [
    'config', 'discovery',
    'server', 'session', 'standalone', 'client', 'multi',
    'node', 'model', 'exit',
]

# Report code coverage one by one for each test group.
root = Path(__file__).parent.parent
report = root/'coverage'/'.coverage'
if report.exists():
    report.unlink()
for group in groups:
    run(
        [
            'uv', 'run',
            'pytest', '--cov', '--cov-append',
            f'tests/test_{group}.py',
        ],
    cwd=root,
)

# Render coverage report locally.
print('Exporting coverage report as HTML.')
folder = root/'build'/'coverage'
folder.mkdir(exist_ok=True, parents=True)
run(
    [
        'uv', 'run',
        'coverage', 'html',
    ],
    cwd=root, check=True,
)
