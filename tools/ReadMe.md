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
example `uv run tools/lint_code.py` to lint the code for quality issues (same
as `uv run ruff check`), `uv run tools/check_types.py` to check type
annotations, etc.

Alternatively, you may also install from source into an existing virtual
environment or even the global Python environment with `uv pip install --group
dev --editable .`. The `--editable` flag makes it so that all code changes take
immediate effect without re-installing the package.

When using Pip, follow the standard workflow: Create a virtual Python
environment `python -m venv .venv`, activate it, and install the project in it
with `pip install --group dev --editable .`

[UV]: https://docs.astral.sh/uv
[Pip]: https://pip.pypa.io


### Releasing a new version

- Bump version number in `pyproject.toml`.
- Add release notes to `docs/releases.md`.
- Add dedicated commit for the version bump.
- Test code and measure coverage:
  ```shell
  ❯ uv run tools/lint_code.py
  ❯ uv run tools/check_types.py
  ❯ uv run tools/render_docs.py
  ❯ uv run tools/build_wheel.py
  ❯ uv run tools/run_tests.py
  ```
- Create pull request and merge.
- Check latest documentation build on Read-the-Docs.
- Fast-forward stable documentation branches:
  ```shell
  ❯ git switch main
  ❯ git pull
  ❯ git branch --force stable
  ❯ git branch --force 1.3
  ❯ git push origin stable
  ❯ git push origin 1.3
  ```
- Publish to PyPI via GitHub Action.
- Create release on GitHub, tag it (like `v1.3.0`), add release notes.
- Report code coverage:
  ```shell
  ❯ uv run tools/measure_coverage.py
  # Add upload token in environment.
  ❯ uv run tools/report_coverage.py`
  ```
