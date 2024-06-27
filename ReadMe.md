# MPh
*Pythonic scripting interface for Comsol Multiphysics*

[Comsol] is a commercial software application that is widely used in
science and industry for research and development. It excels at modeling
almost any (multi-)physics problem by solving the governing set of
partial differential equations via the finite-element method. It comes
with a modern graphical user interface to set up simulation models and
can be scripted from Matlab or its native Java API.

MPh brings the dearly missing power of Python to the world of Comsol.
It leverages the Java bridge provided by [JPype] to access the Comsol
API and wraps it in a layer of pythonic ease-of-use. The Python wrapper
covers common scripting tasks, such as loading a model from a file,
modifying parameters, importing data, to then run the simulation,
evaluate the results, and export them.

Comsol models are marked by their `.mph` file extension, which stands
for multi-physics. Hence the name of this library. It is open-source
and in no way affiliated with Comsol Inc., the company that develops
and sells the simulation software.

Find the full [documentation on Read-the-Docs][docs].

[Comsol]: https://www.comsol.com
[JPype]:  https://github.com/jpype-project/jpype
[docs]:   https://mph.readthedocs.io

[![release page](
    https://img.shields.io/pypi/v/mph.svg?label=release)](
    https://pypi.python.org/pypi/mph)
[![download statistics](
    https://img.shields.io/pypi/dm/MPh)](
    https://pypistats.org/packages/mph)
[![scientific citation](
    https://zenodo.org/badge/264718959.svg)](
    https://zenodo.org/badge/latestdoi/264718959)
[![coverage report](
    https://img.shields.io/codecov/c/github/MPh-py/MPh?token=02ZZ8ZJH3M)](
    https://codecov.io/gh/MPh-py/MPh)
[![latest documentation](
    https://readthedocs.org/projects/mph/badge/?version=latest)](
    https://mph.readthedocs.io/en/latest)

# Settings for ARM-based architectures

COMSOL installed in ARM-based architectures in default, does not resolve the [dynamic libraries] path automatically for running Java program through third party applications. In order to make it work, we have to do it manually. 

As suggested in [COMSOL Multiphysics® Programming Reference Manual] in page 23:
* "On macOS, use the Name DYLD_LIBRARY_PATH and enter the following text in Value: <comsolinstalldir>/ lib/maci64:<comsolinstalldir>/ext/graphicsmagick/maci64:<comsolinstalldir>/ext/ cadimport/maci64, where <comsolinstalldir> is the directory where COMSOL Multiphysics is installed."

We have to do a bit modification as following: 
```bash
DYLD_FALLBACK_LIBRARY_PATH=/Applications/COMSOL62/Multiphysics/lib/macarm64:/Applications/COMSOL62/Multiphysics/ext/graphicsmagick/macarm64:/Applications/COMSOL62/Multiphysics/ext/cadimport/macarm64
```

We can add <code> <b>DYLD_FALLBACK_LIBRARY_PATH</b> </code> environment variable in PyCharm <code> <b> Run/Debug Configuration</b> </code>. 

It works. 



[dynamic libraries]: https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/DynamicLibraryUsageGuidelines.html#//apple_ref/doc/uid/TP40001928-SW10
[COMSOL Multiphysics® Programming Reference Manual]: https://doc.comsol.com/6.2/doc/com.comsol.help.comsol/COMSOL_ProgrammingReferenceManual.pdf&ved=2ahUKEwjv5fffxPuGAxUjQFUIHXKhD8UQFnoECA8QAQ&usg=AOvVaw08MpzY3BkIIfcJLWLuUxaZ


