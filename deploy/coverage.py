"""Measures code coverage by test suite."""
__license__ = 'MIT'


from subprocess import run
from pathlib import Path
from sys import argv


here = Path(__file__).resolve().parent
root = here.parent
file = here/'coverage.sqlite'

rerun  = 'rerun'  in argv[1:]
append = 'append' in argv[1:]

if rerun and not append and file.exists():
    file.unlink()

if file.exists() and not append:
    print('Coverage report already exists.')
else:
    command = ['pytest', '--cov', '--cov-append']
    tests  = ['config', 'discovery', 'server', 'client', 'client-server',
              'stand-alone', 'node', 'model', 'processes']
    for test in tests:
        run(command + [f'tests/test_{test}.py'], cwd=root)

print('Rendering coverage report.')
folder = (here/'coverage').relative_to(root)
run(['coverage', 'html', f'--directory={folder}'], cwd=root)

badge = root/'tests'/file.with_suffix('.svg').name
if badge.exists():
    print('Coverage badge already exists.')
else:
    print('Rendering coverage badge.')
    run(['coverage-badge', '-f', '-o', str(badge)], cwd=root)
