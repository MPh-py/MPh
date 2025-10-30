# Installation

## MPh

MPh is [available on PyPI] and can be readily installed via
```
pip install MPh
```

Requires [JPype] for the bridge from Python to [Comsol's Java API] and [NumPy]
for returning (fast) numerical arrays. Pip makes sure the two Python
dependencies are installed and adds them if missing.

Run `pip uninstall MPh` to remove the package from your system. Note that this
won't uninstall the dependencies.

On Windows, users have encountered problems with the Python installation from
the Microsoft Store ([GitHub issue #57]). In that event, use the Python
installers from [python.org] instead. You will need the 64-bit version of
Python, as is the default, to match Comsol's platform architecture.


## Comsol

Comsol, obviously, you need to license and install yourself.  All major
platforms are supported: Windows, Linux, macOS. [Comsol versions] 6.0 and newer
are expected to work. Up to version 6.3, they have been successfully tested. A
separate Java run-time environment is *not* required as Comsol ships with one
already built in.

Comsol 5.5 and 5.6 may work if you manually downgrade JPype: `pip install
"jpype1<1.6"`. Newer JPype versions no longer support Java 8, which these older
Comsol versions ship with.

Comsol is expected to be installed in the default location suggested by its
installer. Though on Windows, custom locations are also supported, as the
installer stores that information in the central registry, which MPh looks up.

Additionally, whichever Comsol installation starts when you run `comsol` in
the console, will be found as well, even if in a custom location.

If you want to be able to select an alternative Comsol installation via MPh's
API, by passing the `version` argument to [`mph.start()`](#start), and that
Comsol version happens to be installed in a custom location, you can [create a
symbolic link] in `~/.local` on Linux and in `~/Application` on macOS. Have it
point to the corresponding Comsol folder and give the link a name that starts
with `comsol`.

```{note}
For most users who already have a recent Comsol version installed, MPh will
work out of the box.
```


## Licenses

Comsol offers a number of [license options] for its products. Generally
speaking, MPh wants nothing to do with that complication, but rather assumes
that, whichever license you use, things will "just work". That is, you are able
to start the Comsol GUI or invoke any of its command-line tools without extra
configuration. Because Comsol's license management handles that in one way or
another. This is true for the most common license types: "CPU-Locked" and
"Floating Network".

For more outlandish license types, that may not be the case. For example, the
"Class Kit" license requires users to pass the command-line argument `-ckl`
when starting Comsol. In this particular case, you can tell MPh to do the same,
by setting [`mph.option('classkit', True)`](#option) before calling
[`mph.start()`](#start). In other such cases, [open an issue] if you want to
add support to the code base.


[available on PyPI]:      https://pypi.python.org/pypi/mph
[JPype]:                  https://jpype.readthedocs.io
[Comsol's Java API]:      https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[NumPy]:                  https://numpy.org
[GitHub issue #57]:       https://github.com/MPh-py/MPh/issues/57
[python.org]:             https://python.org
[Comsol versions]:        https://www.comsol.com/release-history
[Apple Silicon]: https://en.wikipedia.org/wiki/Apple_silicon
[GitHub issue #80]:       https://github.com/MPh-py/MPh/issues/80
[create a symbolic link]: https://www.howtogeek.com/287014/how-to-create-and-use-symbolic-links-aka-symlinks-on-linux/
[license options]:        https://www.comsol.com/products/licensing
[open an issue]:          https://github.com/MPh-py/MPh/issues
