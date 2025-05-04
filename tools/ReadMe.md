## Developer tools

These are simple helper scripts to run the various development tools, such
as pyTest, Flit, and Sphinx. See the doc-strings of the individual scripts
for details.


### Running tests

MPh can be used and tested from source, provided NumPy, JPype, and pyTest
are already installed. That is, the following runs the test suite for what
is currently in the `main` branch:
```
❯ git clone https://github.com/MPh-py/MPh.git
❯ cd MPh
❯ python tools/test.py --log
```

This works because when you are in the project folder (named `MPh`),
then `import mph` will find the subfolder `mph` and run the code from
there, possibly ignoring a different MPh version installed in the
Python environment.

Note that just calling `pytest` will fail as the test suite starts a Comsol
client, and hence the Java VM, multiple times, which JPype does not support.
The `test.py` script works around that by starting a new subprocess each time.


### Local development

If you also want to build the documentation locally, or render the
code-coverage report, or build the wheel, it's best to create a dedicated
virtual environment:
```
❯ python -m venv venv
❯ venv/Scripts/activate                  # Windows
❯ source venv/bin/activate               # Linux/macOS
❯ pip install --group dev --editable .
```

This installs MPh and all its development dependencies inside that new
environment, in the newly created `venv` sub-folder. The `dev` dependency group
is defined in `pyproject.toml`. The `--editable` flag makes it so that all code
changes take immediate effect without re-installing the package.


### Releasing a new version

- Bump version number in `pyproject.toml`.
- Add release notes to `docs/releases.md`.
- Add dedicated commit for the version bump.
- Tag commit with version number, e.g. `git tag v1.2.0`
- Force `stable` branch to latest commit: `git branch -f stable`
- Same for the current documentation branch: `git branch -f 1.2`
- Run code linter: `python tools/lint.py`
- Test docs build: `python tools/docs.py`
- Test wheel build: `python tools/wheel.py`
- Run code coverage: `python tools/coverage.py`
- Push to GitHub:
```
git push origin main
git push --tags
git push origin stable
git push origin 1.2
```
- Upload coverage report: `python tools/codecov.py`
- Create new release on GitHub and add release notes.
- Publish to PyPI: `python tools/publish.py`
