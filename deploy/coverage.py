"""Measures code coverage by test suite."""
__license__ = 'MIT'

from subprocess import run
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parent

file = here/'coverage.sqlite'
if file.is_file():
    print('Rendering coverage report.')
    folder = (here/'coverage').relative_to(root)
    run(['coverage', 'html', f'--directory={folder}'], cwd=root)
    badge = root/'tests'/file.with_suffix('.svg').name
    if badge.exists():
        print('Coverage badge already exists.')
    else:
        print('Rendering coverage badge.')
        run(['coverage-badge', '-f', '-o', str(badge)], cwd=root)
else:
    command = ['pytest', '--cov', '--cov-append']
    tests = ['discovery', 'server', 'session', 'node', 'model', 'processes']
    for test in tests:
        run(command + [f'tests/test_{test}.py'], cwd=root)
