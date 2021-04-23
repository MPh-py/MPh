Steps to take when releasing a new version:
* Bump version number and enter current date in `mph/__init__.py`.
* Add a dedicated commit for the version bump.
* Add the release notes for this version in the same commit.
* Tag the commit with the version number, for example: `git tag -a v1.0.1`.
* Enter the release notes as an annotation.
* Push the commit (but not the tag): `git push origin main`.
* Check that documentation built successfully on Read-the-Docs.
* Publish to PyPI by running `deploy/publish.py`.
* Check that meta information is correct on PyPI.
* Then push the tag: `git push --tags`.
* Create a new release on GitHub and add the release notes.
* Push the `stable` branch to the new release tag.
