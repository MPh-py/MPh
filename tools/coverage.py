"""
Measures code coverage by test suite.

We cannot just run pyTest on the entire test suite (in the `tests` folder
of the repo) because the individual scripts there all start a client in
their respective setup routine. That is, they all start the Java VM,
which will fail once pyTest gets to the second script in the sequence.
Instead, we run pyTest for each test group separately, with the coverage
plug-in enabled, and thus generate the coverage report incrementally.

We also render the coverage report (in `.coverage`) as static HTML for
easy inspection. This is helpful during development. Find it in the
`build/coverage` folder.

The coverage report may be uploaded to the online service CodeCov. This is
usually only done for a new release, but could also happen on each commit.
There's a separate script, `codecov.py`, to automate that.
"""

from subprocess import run
from pathlib    import Path
from sys        import executable as python
from os         import environ, pathsep


# Define order of test groups.
groups = ['config', 'discovery', 'server', 'session', 'standalone', 'client',
          'multi', 'node', 'model', 'exit']

# Run MPh in source tree, not a possibly different version installed elsewhere.
root = Path(__file__).resolve().parent.parent
if 'PYTHONPATH' in environ:
    environ['PYTHONPATH'] = str(root) + pathsep + environ['PYTHONPATH']
else:
    environ['PYTHONPATH'] = str(root)

# Report code coverage one by one for each test group.
report = root/'.coverage'
if report.exists():
    report.unlink()
for group in groups:
    run([python, '-m', 'pytest', '--cov', '--cov-append',
         f'tests/test_{group}.py'], cwd=root)

# Render coverage report locally.
print('Exporting coverage report as HTML.')
folder = root/'build'/'coverage'
folder.mkdir(exist_ok=True, parents=True)
run(['coverage', 'html', f'--directory={folder}'], cwd=root, check=True)
