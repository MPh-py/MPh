Limitations
-----------

This library depends on the Python-to-Java bridge [JPype][jpype-repo].
It therefore inherits its limitation, in that only one Java virtual
machine can be managed within the same Python session, and thus only
one Comsol client. If several simulations are to be run in parallel,
distributed over independent processor cores in an effort to achieve
maximum speed-up of a parameter sweep, they have to be started as
separate Python (sub-)processes. This is a feasible work-around, but
a limitation nonetheless.

For the same reason, it seems, the [unit tests][mph-tests] that
come with MPh fail when collected and run via the testing framework
[pyTest][pytest-docs]. They must be run directly from the command
line. Since they cannot be used for continuous integration testing
anyway, given that they depend on Comsol being installed on the local
machine, this is but a minor inconvenience.

There is an alternative Java bridge, [pyJNIus][jnius-repo], which is
not limited to one virtual machine, but then fails in another regard:
A number of Java methods exposed by Comsol are inexplicably missing
from the Python encapsulation.

MPh is, at this point, also limited to work on Windows only, even
though Comsol itself is available on other platforms, namely Linux
and MacOS. The code that identifies installed Comsol versions and
locates the executables would have to be adapted to support the
other operating systems. This is not particularly difficult for
someone with access to a test environment. Contributions or even
just suggestions [on GitHub][mph-repo] are welcome.

Cross-network client–server connections, while ostensibly supported
by this library, have never actually been tested — for lack of a
network license, required for that purpose. It may work as is, or may
require transmitting login details: user name and password. File a
GitHub issue if you are in a position to test this scenario and want
the problem solved.

The API is intentionally scope-limited to automating the simulation
workflow, such as running parameter sweeps or optimization routines
with customized, Python-powered post-processing. Exposing any and all
Comsol features to create or alter every aspect of a model, and thus
replicating the entire Java API, albeit in a more pythonic way, is out
of scope.

Though users who do want to dig deeper may access the "pythonized"
Java layer directly, via the `.java` attribute of `Client` instances
(mapping to Comsol's `ModelUtil`) as well as `Model` (mapping to
Comsol's `model`). Refer to Comsol's programming manual for details.

This might even be worthwhile for Java developers, as the interactive
Python prompt provides easy introspection of the object hierarchy and
lets them learn by doing. In these circumstances, one might find the
convenience function `mph.inspect` helpful, as it not only lists an
object's methods in a more readable way than the built-in `dir`, but
also displays the "properties" possibly defined on a model node. Keep
in mind, however, that JPype cannot perform all type conversions
silently in the background. Occasionally, when there is ambiguity in
overloaded methods, you will have to cast types explicitly. Refer to
the [JPype documentation][jpype-docs] for help.


[mph-repo]:    https://github.com/john-hennig/mph
[mph-tests]:   https://github.com/John-Hennig/mph/tree/master/tests
[jpype-repo]:  https://github.com/jpype-project/jpype
[jpype-docs]:  https://jpype.readthedocs.io
[jnius-repo]:  https://github.com/kivy/pyjnius
[jnius-docs]:  https://pyjnius.readthedocs.io
[pytest-docs]: https://docs.pytest.org
