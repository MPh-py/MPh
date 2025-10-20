"""
Uploads the coverage report to CodeCov.

The script expects the CodeCov uploader to be installed locally. On Windows,
for example, `codecov.exe` would have to be on the search path. It also expects
the CodeCov upload token for this project to be set as an environment variable.

CodeCov does not accept Coverage.py's standard report format, i.e. the
`.coverage` file. It must be converted to XML format beforehand.
"""

from subprocess import run
from pathlib    import Path
from os         import environ


token = environ.get('MPh_CodeCov_token', None)
if not token:
    raise RuntimeError('CodeCov upload token not set in environment.')

root = Path(__file__).parent.parent
run(['coverage', 'xml'], cwd=root, check=True)
run(
    ['codecov', '--file', 'coverage.xml', '--token', token],
    cwd=root, check=True,
)
