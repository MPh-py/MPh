"""Tests the exit behavior of the process."""

########################################
# Dependencies                         #
########################################
import parent # noqa F401
from subprocess import run, PIPE
from pathlib import Path
from sys import argv
from sys import executable as python
import logging


########################################
# Fixtures                             #
########################################

def run_script(name):
    # Runs the named script from the project's root folder so that coverage
    # reporting doesn't get confused about source file locations.
    here = Path(__file__).resolve().parent
    file = here/name
    assert file.is_file()
    assert file.suffix == '.py'
    root = here.parent
    process = run([python, str(file)], cwd=root,
                  stdout=PIPE, stderr=PIPE, universal_newlines=True)
    return process


########################################
# Tests                                #
########################################

def test_exit_nojvm_sys():
    process = run_script('exit_nojvm_sys.py')
    assert process.returncode == 2


def test_exit_nojvm_exc():
    process = run_script('exit_nojvm_exc.py')
    assert process.returncode == 1
    assert process.stderr.strip().startswith('Traceback')
    assert process.stderr.strip().endswith('RuntimeError')


def test_exit_client_sys():
    process = run_script('exit_client_sys.py')
    assert process.returncode == 2


def test_exit_client_exc():
    process = run_script('exit_client_exc.py')
    assert process.returncode == 1
    assert process.stderr.strip().startswith('Traceback')
    assert process.stderr.strip().endswith('RuntimeError')


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

    test_exit_nojvm_sys()
    test_exit_nojvm_exc()
    test_exit_client_sys()
    test_exit_client_exc()
