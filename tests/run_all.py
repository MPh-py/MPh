"""Runs all tests in the intended order."""
__license__ = 'MIT'

from subprocess import run
from pathlib    import Path
from platform   import system
from sys        import argv

tests  = ['discovery', 'server', 'session', 'node', 'model', 'processes']
here   = Path(__file__).parent
python = 'python' if system() == 'Windows' else 'python3'
for test in tests:
    print(f'test_{test}')
    process = run([python, f'test_{test}.py'] + argv[1:], cwd=here)
    if process.returncode == 0:
        print('Passed.')
    else:
        print('Failed.')
    print()
