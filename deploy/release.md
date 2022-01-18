﻿Steps to take when releasing a new version:
* Bump version number in `mph/meta.py`.
* Add release notes to `docs/releases.md`.
* Add dedicated commit for the version bump.
* Push to GitHub: `git push origin main`.
* Check documentation build on Read-the-Docs.
* Tag commit with version number, e.g. `git tag v1.1.1`.
* Push the new tag: `git push --tags`.
* Activate, but hide, build for the tag on Read-the-Docs.
* Force `stable` branch to new release tag: `git branch -f stable`.
* Same for the current documentation branch: `git branch -f 1.1`.
* Push both branches upstream, e.g. `git push origin stable`.
* Run code coverage and upload report to CodeCov.
* Create new release on GitHub and add release notes.
* Publish to PyPI by running `deploy/publish.py`.
* Check that meta information is correct on PyPI.
