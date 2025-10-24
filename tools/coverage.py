"""
Measures code coverage by test suite.

We cannot just run pyTest on the entire test suite (in the `tests` folder of
the repo) because many of the individual test scripts there start a Comsol
client in their respective setup routine. That is, they start the Java VM,
which will fail once pyTest gets to the second script in the sequence because
JPype doesn't allow that within the same Python process.

Instead, we run pyTest for each test group separately, with the coverage
plug-in enabled, and thus generate the coverage report incrementally.

We also render the coverage report as static HTML for easy inspection. This is
helpful during development. Find it in the `build/coverage` folder.

The coverage report may be uploaded to the online service CodeCov. This is
usually only done for a new release, but could also happen on each commit.
There's a separate script, `codecov.py`, to take care of that whenever needed.
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
            'uv', 'run',  '--no-sync',
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
        'uv', 'run',  '--no-sync',
        'coverage', 'html', f'--directory={folder}',
    ],
    cwd=root, check=True,
)
