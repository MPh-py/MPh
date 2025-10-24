"""
Uploads the coverage report to CodeCov.

The script expects the CodeCov upload token for this project to be set as an
environment variable.

CodeCov does not accept Coverage.py's standard report format, i.e. the
`.coverage` file, which is why it must be converted to XML for the upload.
"""

from subprocess import run
from pathlib    import Path
from os         import environ


token = environ.get('MPh_CodeCov_token', None)
if not token:
    raise RuntimeError('CodeCov upload token not set in environment.')

root = Path(__file__).parent.parent
run(['uv', 'run', '--no-sync', 'coverage', 'xml'], cwd=root, check=True)
run(
    [
        'uv', 'run',  '--no-sync',
        'codecov',
        '--file', 'build/coverage/coverage.xml',
        '--token', token,
    ],
    cwd=root, check=True,
)
