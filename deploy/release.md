Steps to take when releasing a new version:
* Bump version number and enter current date in `mph/__init__.py`.
* Add the release notes to `docs/releases.md`.
* Add a dedicated commit for the version bump.
* Push to GitHub: `git push origin main`.
* Check that documentation built successfully on Read-the-Docs.
* Publish to PyPI by running `deploy/publish.py`.
* Check that meta information is correct on PyPI.
* Tag the commit with the version number, for example: `git tag v1.0.4`.
* Then push the tag: `git push --tags`.
* Activate, but hide, the build for the tag on Read-the-Docs.
* Force the `stable` branch to new release tag: `git branch -f stable`.
* Same for the current documentation branch: `git branch -f 1.0`.
* Push both branches upstream, e.g.: `git push origin stable`.
* Create a new release on GitHub and add the release notes.
