# Installation

## MPh

MPh is [available on PyPI] and can be readily installed via
```
pip install MPh
```

Requires [JPype] for the bridge from Python to [Comsol's Java API]
and [NumPy] for returning (fast) numerical arrays. Pip makes sure the
two Python dependencies are installed and adds them if missing.

Run `pip uninstall MPh` to remove the package from your system. Note
that this won't uninstall the dependencies.


## Comsol

Comsol, obviously, you need to license and install yourself. [Versions]
5.5 and newer are expected to work. Up to version 6.1, they have been
successfully tested — at one point or another. A separate Java run-time
environment is *not* required as Comsol ships with one already built in.

All major platforms are supported: Windows, Linux, macOS. Though
ARM-based architectures are not, namely Apple Silicon on M1/M2 Macs.
(Contribute to solving [GitHub issue #80] if you want to remedy that.)
Linux support has only been rigorously tested on Ubuntu. Occasional
problems may occur on other distributions. Specifically with image
exports, for which Comsol depends on external libraries.

Comsol is expected to be installed in the default location suggested by
its installer. Though on Windows, custom locations are also supported,
as the installer stores that information in the central registry, which
MPh looks up.

Additionally, whichever Comsol installation starts when you run `comsol`
in the console, will be found as well, even if in a custom location.

If you want to be able to select an alternative Comsol installation via
MPh's API, by passing the `version` argument to [`mph.start()`](#start),
and that Comsol version happens to be installed in a custom location,
you can [create a symbolic link] in `~/.local` on Linux and in
`~/Application` on macOS. Have it point to the corresponding Comsol
folder and give the link a name that starts with `comsol`.


## Licenses

Comsol offers a number of [license options] for its products.
Generally speaking, MPh assumes that, whichever license you use,
things will "just work". That is, you are able to start the Comsol GUI
or invoke any of its command-line tools without extra configuration.
Because Comsol's license management handles that in one way or another.
This is true for the most common license types: "CPU-locked" and
"floating network".

For other license types, that may not be the case. For example, the
"class kit" license requires you to pass the command-line argument
`-ckl` when starting Comsol. In this particular case, you can tell MPh
to do the same, by setting [`mph.option('classkit', True)`](#option)
before calling [`mph.start()`](#start).

Other "unusual" license types may not be supported. If you want to
change that, [open an issue] and explain how they are different.


[available on PyPI]:      https://pypi.python.org/pypi/mph
[JPype]:                  https://jpype.readthedocs.io
[Comsol's Java API]:      https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[NumPy]:                  https://numpy.org
[Versions]:               https://www.comsol.com/release-history
[GitHub issue #80]:       https://github.com/MPh-py/MPh/issues/80
[create a symbolic link]: https://www.howtogeek.com/287014
[license options]:        https://www.comsol.com/products/licensing
[open an issue]:          https://github.com/MPh-py/MPh/issues
