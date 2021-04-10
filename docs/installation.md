# Installation

MPh is [available on PyPI][pypi] and can be readily installed via
```none
pip install MPh
```
Run `pip uninstall MPh` in order to remove the package from your system.

Requires [JPype][jpype] for the bridge from Python to [Comsol's
Java API][japi] and [NumPy][numpy] for returning (fast) numerical arrays.
`pip` makes sure the two Python dependencies are installed and adds them
if missing.

Comsol, obviously, you need to license and install yourself. Versions
from Comsol 5.1 onward are expected to work. A separate Java run-time
environment is *not* required as Comsol ships with one already built in.

On Linux and macOS, Comsol is expected to be found in its respective
default location. On Windows, any custom install location is supported,
as the installer stores that information in the central registry.


[pypi]:  https://pypi.python.org/pypi/mph
[jpype]: https://jpype.readthedocs.io
[japi]:  https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[numpy]: https://numpy.org
