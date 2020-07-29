"""Deletes cache and build artifacts."""
__license__ = 'MIT'


from pathlib import Path
import winshell


def delete(target, confirm=False, silent=False):
    """Deletes a file or folder."""
    winshell.delete_file(str(target), no_confirm=not confirm, silent=silent)


main = Path(__file__).absolute().parent.parent

for folder in main.rglob('__pycache__'):
    delete(folder)

for folder in main.rglob('.pytest_cache'):
    delete(folder)

for folder in (main/'dist', main/'docs'/'rendered'):
    if folder.exists():
        delete(folder)
