"""
Measures code coverage by test suite.

We cannot just run pyTest on the entire test suite (in the `tests` folder
of the repo) because the individual scripts there all start a client in
their respective setup routine. That is, they all start the Java VM,
which will fail once pyTest gets to the second script in the sequence.
Instead, we run pyTest for each test group separately, with the coverage
plug-in enabled, and thus generate the coverage report incrementally.

We also render the coverage report (in `.coverage`) as HTML for easy
inspection. This is helpful during development.

The coverage report may be uploaded to the online service CodeCov. This is
usually only done for a new release, but could also happen on each commit.
There's a separate script, `codecov.py`, to automate that.
"""

from subprocess import run
from pathlib    import Path
from sys        import executable as python
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

# Report code coverage one by one for each test group.
report = root/'.coverage'
if report.exists():
    report.unlink()
for group in groups:
    run([python, '-m', 'pytest', '--cov', '--cov-append',
         f'tests/test_{group}.py'], cwd=root)

# Render coverage report locally.
print('Exporting coverage report as HTML.')
folder = (here/'coverage').relative_to(root)
run(['coverage', 'html', f'--directory={folder}'], cwd=root)
