"""Runs all tests in the intended order."""
__license__ = 'MIT'

from subprocess import run
from pathlib    import Path
from platform   import system
from sys        import argv
from timeit     import default_timer as now

tests  = ['config', 'discovery', 'server', 'client', 'client-server',
          'stand-alone', 'node', 'model', 'processes']
here   = Path(__file__).parent
python = 'python' if system() == 'Windows' else 'python3'
for test in tests:
    print(f'test_{test}')
    t0 = now()
    process = run([python, f'test_{test}.py'] + argv[1:], cwd=here)
    if process.returncode == 0:
        print(f'Passed in {now()-t0:.0f} s.')
    else:
        print(f'Failed after {now()-t0:.0f} s.')
    print()
