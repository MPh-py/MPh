"""Tests multi-processing."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent # noqa F401
from subprocess import run, PIPE
from platform import system
from pathlib import Path
from sys import argv
import logging


########################################
# Globals                              #
########################################
here   = Path(__file__).parent
python = 'python' if system() == 'Windows' else 'python3'


########################################
# Tests                                #
########################################

def test_exit_sys():
    process = run([python, 'exit_sys.py'], stdout=PIPE, stderr=PIPE, cwd=here)
    exit_code = process.returncode
    assert exit_code == 2


def test_exit_exc():
    process = run([python, 'exit_exc.py'], stdout=PIPE, stderr=PIPE, cwd=here)
    exit_code = process.returncode
    assert exit_code == 1
    stderr = process.stderr.decode().strip()
    assert stderr.startswith('Traceback')
    assert stderr.endswith('RuntimeError')


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG if 'debug' in arguments else logging.INFO,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_exit_sys()
    test_exit_exc()
