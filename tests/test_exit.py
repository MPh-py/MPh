"""Tests the exit behavior of the process."""

from fixtures   import setup_logging

from subprocess import run
from pathlib    import Path
from sys        import executable as python


def run_script(name: str):
    # Runs the named script from the project's root folder so that coverage
    # reporting doesn't get confused about source file locations.
    here = Path(__file__).resolve().parent
    file = here/name
    assert file.is_file()
    assert file.suffix == '.py'
    root = here.parent
    process = run([python, file], cwd=root, capture_output=True, text=True)
    return process


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


if __name__ == '__main__':
    setup_logging()
    test_exit_nojvm_sys()
    test_exit_nojvm_exc()
    test_exit_client_sys()
    test_exit_client_exc()
