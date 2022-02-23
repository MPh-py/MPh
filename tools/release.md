Steps to take when releasing a new version:
* Bump version number in `mph/meta.py`.
* Add release notes to `docs/releases.md`.
* Add dedicated commit for the version bump.
* Tag commit with version number, e.g. `git tag v1.1.4`.
* Force `stable` branch to latest commit: `git branch -f stable`.
* Same for the current documentation branch: `git branch -f 1.1`.
* Run code linter: `pflake8`.
* Test docs build: `python tools/docs.py`.
* Test wheel build: `python tools/wheel.py`.
* Run tests for each supported Python/OS: `python3x tools/test.py`.
* Run code coverage: `python tools/coverage.py`.
* Push to GitHub:
```console
    git push origin main
    git push --tags
    git push origin stable
    git push origin 1.1
```
* Upload coverage report: `python tools/codecov.py`.
* Create new release on GitHub and add release notes.
* Publish to PyPI: `python tools/publish.py`.
