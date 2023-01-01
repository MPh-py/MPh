## Test suite

The scripts here, along with some fixtures, constitute the test suite.
They are run in the intended order by the helper scripts `test.py` and
`coverage.py` in the `tools` folder.

Note that when running those scripts from the project folder, i.e. the
parent folder of this one here, then they will test what's inside the
`mph` folder, i.e. the current source code. If run from anywhere else,
they would test whatever `import mph` finds, which may be an installed
version of MPh. This behavior is intentional, so that new code can be
tested without touching the installed version, even without a separate
virtual environment.

