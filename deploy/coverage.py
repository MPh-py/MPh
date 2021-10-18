"""
Measures code coverage by test suite.

We cannot just run pyTest on the entire test suite (in the `tests` folder
of the repo) because the individual scripts there all start a client in
their respective setup routine. That is, they all start the Java VM,
which will fail once pyTest gets to the second script in the sequence.
Instead, we run pyTest for each script separately, with the coverage
plug-in enabled, and generate the coverage report incrementally.

If the coverage report file (`coverage.xml`) already exists, we instead
render it as HTML for inspection. This is helpful during development.
The coverage report may also be uploaded to an online service such as
CodeCov for each published release or even commit.
"""

from subprocess import run
from pathlib import Path
import sys

tests = ['meta', 'config', 'discovery', 'server', 'session', 'standalone',
         'client', 'multi', 'node', 'model', 'exit']

here   = Path(__file__).resolve().parent
root   = here.parent
file   = root/'coverage.xml'
python = sys.executable
if not file.exists():
    command = [python, '-m', 'pytest',
               '--cov', '--cov-append', '--cov-report', 'xml']
    for test in tests:
        run(command + [f'tests/test_{test}.py'], cwd=root)
else:
    print('Rendering existing coverage report as HTML.')
    folder = (here/'coverage').relative_to(root)
    run(['coverage', 'html', f'--directory={folder}'], cwd=root)
