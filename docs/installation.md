# Installation

MPh is [available on PyPI] and can be readily installed via
```
pip install MPh
```

Run `pip uninstall MPh` to remove the package from your system.

Requires [JPype] for the bridge from Python to [Comsol's Java API]
and [NumPy] for returning (fast) numerical arrays. Pip makes sure the
two Python dependencies are installed and adds them if missing.

Comsol, obviously, you need to license and install yourself. Versions
5.5 and newer are expected to work, i.e. have been tested. A separate
Java run-time environment is *not* required as Comsol ships with one
already built in.

Comsol is expected to be installed in the default location suggested by
its installer. Though on Windows, custom locations are also supported,
as the installer stores that information in the central registry, which
MPh looks up.

Additionally, whichever Comsol installation starts when you run `comsol`
in the console, will be found as well, even if in a custom location.

If you want to be able to select an alternative Comsol installation via
MPh's API, like by passing the `version` option to {func}`mph.start`,
and that Comsol version happens to be installed in a custom location,
you can [create a symbolic link] in `~/.local` on Linux and in
`~/Application` on macOS. Have it point to the corresponding Comsol
folder and give the link a name that starts with `comsol`.


[available on PyPI]:      https://pypi.python.org/pypi/mph
[JPype]:                  https://jpype.readthedocs.io
[Comsol's Java API]:      https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[NumPy]:                  https://numpy.org
[create a symbolic link]: https://www.howtogeek.com/287014
