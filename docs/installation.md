Installation
------------

MPh is [available on PyPI][dist] and can be readily installed via `pip`:
```none
pip install mph
```
Add `--user` to the above command to make it a per-user installation,
instead of system-wide, which may or may not be preferable. Run
```none
pip uninstall mph
```
in order to remove the library from your system.

Requires [JPype][jpype] for the bridge from Python to [Comsol's
Java API][java] and [NumPy][numpy] for returning (fast) numerical arrays.
`pip` makes sure the two Python dependencies are installed and adds them
if missing.

Comsol, obviously, you need to license and install yourself. Versions
from Comsol 5.3 onward are expected to work. If you want to use the
client–server mode, make sure to once run `comsolmphserver` from a
console first to enter the obligatory user name and password.


[dist]:  https://pypi.python.org/pypi/mph
[jpype]: https://jpype.readthedocs.io
[java]:  https://www.comsol.com/blogs/automate-modeling-tasks-comsol-api-use-java/
[numpy]: https://numpy.org
