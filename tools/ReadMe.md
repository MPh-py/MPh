## Developer tools

These are simple helper scripts to run the various development tools, such
as the test suite, the type checker, code linter, and documentation builder.
See the doc-strings of the individual scripts for details.


### Local development

To use any of the dev tools, you should install the project locally from
source. It is recommended to use [UV] to manage the project, though installing
it via [Pip] remains possible as well.

Install UV globally on your machine, for example with `winget install
astral-sh.uv` on Windows, `curl -LsSf https://astral.sh/uv/install.sh | sh`
on Linux, and `brew install uv` on macOS. Then `git clone` this repository
and run `uv sync` in the project root folder. It will create a virtual
environment in the `.venv` folder with all dependencies installed in it, as
defined in `pyproject.toml`.

Run any of the dev tools via the helper scripts in the `tools` folder. For
example `uv run tools/lint.py` to lint the code (same as `uv run ruff check`),
`uv run tools/types.py` to check types, etc.

You may also install into an existing virtual environment or even the global
Python environment with `uv pip install --editable .`. The `--editable` flag
makes it so that all code changes take immediate effect without re-installing
the package.

When using Pip, follow the standard workflow: Create a virtual Python
environment `python -m venv .venv`, activate it, and install the project in it
with `pip install --editable .`

[UV]: https://docs.astral.sh/uv
[Pip]: https://pip.pypa.io

### Releasing a new version

- Bump version number in `pyproject.toml`.
- Add release notes to `docs/releases.md`.
- Add dedicated commit for the version bump.
- Tag commit with version number, e.g. `git tag v1.3.0`
- Force `stable` branch to latest commit: `git branch -f stable`
- Same for the current documentation branch: `git branch -f 1.3`
- Run code linter: `uv run tools/lint.py`
- Test docs build: `un run tools/docs.py`
- Test wheel build: `uv run tools/wheel.py`
- Run code coverage: `uv run tools/coverage.py`
- Push to GitHub:
```
git push origin main
git push --tags
git push origin stable
git push origin 1.3
```
- Upload coverage report: `uv run tools/codecov.py`
- Create new release on GitHub and add release notes.
- Publish to PyPI: `uv run tools/publish.py`
