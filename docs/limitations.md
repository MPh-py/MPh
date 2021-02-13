Limitations
-----------

### Java bridge

This library depends on the Python-to-Java bridge [JPype][jpype].
It therefore inherits its limitation, in that only one Java virtual
machine can be managed within the same Python session, and thus only
one Comsol client. If several simulations are to be run in parallel,
distributed over independent processor cores in an effort to achieve
maximum speed-up of a parameter sweep, they have to be started as
separate Python (sub-)processes. This is a feasible work-around, but
a limitation nonetheless.

For the same reason, the [unit tests][tests] that come with MPh fail
when collected and run via the testing framework [pyTest][pytest].
They must be run directly from the command line. Since they cannot be
used for continuous integration testing anyway, given that they depend
on Comsol being installed on the local machine, this is but a minor
inconvenience.

Furthermore, there are some known, but unresolved issues with JPype's
shutdown of the Java virtual machine. Most notably, pressing
<kbd>Ctrl+C</kbd> to interrupt an ongoing operation will usually crash
the entire Python session. So do not rely on that to work.

(There is an alternative Java bridge, [pyJNIus][jnius], which is
not limited to one virtual machine, but then fails in another regard:
A number of Java methods exposed by Comsol are inexplicably missing
from the Python encapsulation.)


### Creating models

The API is intentionally scope-limited to automating the simulation
workflow, such as running parameter sweeps or optimization routines
with customized, Python-powered post-processing. Exposing any and all
Comsol features to create or alter every aspect of a model, and thus
replicating the [entire Java API][japi], albeit in a more pythonic way,
is out of scope.

Though users who do want to dig deeper may access the "pythonized"
Java layer directly, via the `.java` attribute of `Client` instances
(mapping to Comsol's `ModelUtil`) as well as `Model` (mapping to
Comsol's `model`). Refer to Comsol's programming manual for details.

This might even be worthwhile for Java developers of Comsol
applications, as the interactive Python prompt provides easy
introspection of the object hierarchy. In these circumstances, one
might find the convenience function `mph.inspect` helpful, as it not
only lists an object's methods in a more readable way than Python's
built-in `dir`, but also displays the "properties" possibly defined
on a model node.

In that event, it may equally help to call the returned Python model
object something like `pymodel` and assign the name `model` to
`pymodel.java`. Then you can just copy-and-paste Java (or even Matlab)
code from the Comsol Programming Manual or as exported from the Comsol
front-end. Python will gracefully overlook gratuitous semicolons at
the end of statements, so this approach would even work for entire
blocks of code. Keep in mind, however, that JPype cannot perform all
type conversions silently in the background. Occasionally, when there
is ambiguity in overloaded methods, you will have to cast types
explicitly. Refer to the [JPype documentation][jpype] for help.


### Client-server mode

In addition to running a stand-alone Comsol client, MPh also supports
client–server connections. Client and server may either run on the
same machine (which may or may not have benefits in terms of memory
overhead) or they may communicate across the network. Note, however,
that the latter scenario has never actually been tested — for lack of
a network license required for that purpose. It may work as is, or may
require transmitting login details: user name and password. File a
[GitHub issue][issues] if you are in a position to test this and want
the problem solved.


### Linux support

On Linux, the stand-alone Comsol client (as opposed to a client
connecting to a server) will fail to start if all you did was install
MPh. You will also have to add the names of shared-library folders to
the environment variable `LD_LIBRARY_PATH` and explicitly `export` it.
Otherwise initialization of the stand-alone client will throw a
`java.lang.UnsatisfiedLinkError` because required external libraries
cannot be found.

Add the following lines at the end of your shell configuration file,
such as `.bashrc`:
```shell
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:\
/usr/local/comsol56/multiphysics/lib/glnxa64:\
/usr/local/comsol56/multiphysics/ext/graphicsmagick/glnxa64
```

Clearly, these paths depend on the installed Comsol version and will
have to be adapted accordingly.

Requiring this variable to be set correctly limits the possibility
of selecting a specific back-end from within MPh, as adding multiple
installations to that search path would very likely lead to name
collisions. Ideally, starting a stand-alone client would work out of
the box, without the above manual configuration. However,
[this issue][issue8] is currently unresolved.


### macOS support

Support for macOS is experimental and entirely untested. The
implementation is nearly identical to the one for Linux, and only
deviates wherever the Comsol documentation indicates a difference in
naming. As such, the environment variable for the library search
path is instead called `DYLD_LIBRARY_PATH`, and Comsol would typically
be found in, e.g., `/Applications/COMSOL56/Multiphysics`. Adjust your
shell configuration accordingly. And please report back on the
corresponding [Github issue][issue9] if you were able to test this.


[repo]:   https://github.com/john-hennig/mph
[tests]:  https://github.com/John-Hennig/mph/tree/master/tests
[jpype]:  https://jpype.readthedocs.io
[jnius]:  https://pyjnius.readthedocs.io
[pytest]: https://docs.pytest.org
[japi]:   https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[issues]: https://github.com/John-Hennig/MPh/issues
[issue8]: https://github.com/John-Hennig/MPh/issues/8
[issue9]: https://github.com/John-Hennig/MPh/issues/9
