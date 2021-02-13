"""Tests running multiple processes."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import parent
from subprocess import run, PIPE
import platform
import logging
from sys import argv


########################################
# Globals                              #
########################################
logger = logging.getLogger(__name__)
python = 'python' if platform.system() == 'Windows' else 'python3'


########################################
# Tests                                #
########################################

def test_exit_sys():
    logger.info('Testing exit code of external process.')
    process = run([python, 'exit_sys.py'], stdout=PIPE, stderr=PIPE)
    exit_code = process.returncode
    logger.info(f'Process exited with code {exit_code}.')
    assert exit_code == 2


def test_exit_exc():
    logger.info('Testing external process raising an unhandled exception.')
    process = run([python, 'exit_exc.py'], stdout=PIPE, stderr=PIPE)
    exit_code = process.returncode
    logger.info(f'Process exited with code {exit_code}.')
    assert exit_code == 1
    stderr = process.stderr.decode().strip()
    assert stderr.startswith('Traceback')
    assert stderr.endswith('RuntimeError')
    logger.info('Error traceback is as expected.')


########################################
# Main                                 #
########################################

if __name__ == '__main__':

    arguments = argv[1:]
    if 'log' in arguments or 'debug' in arguments:
        logging.basicConfig(
            level   = logging.DEBUG,
            format  = '[%(asctime)s.%(msecs)03d] %(message)s',
            datefmt = '%H:%M:%S')

    test_exit_sys()
    test_exit_exc()
