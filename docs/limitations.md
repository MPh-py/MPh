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


### Platform differences

The Comsol API offers two distinct ways to run a simulation session
on the local machine. One may either start a "stand-alone" client,
which does not require a Comsol server. Or one may start a server
separately and have a "thin" client connect to it via a loop-back
network socket. The first approach is more lightweight and arguably
more robust, as it keeps everything inside the same process. The
second approach is slower to start up and relies on the inter-process
communication to work, but would also work across the network, i.e.,
for remote sessions where the client runs locally and delegates the
heavy lifting to a server running on another machine. If we instantiate
the `Client` class without providing a value for the `host` address and
network `port`, it will create a stand-alone client. Otherwise it will
run in client–server mode.

On Linux and macOS however, the stand-alone mode does not work out of
the box. This is due to a limitation of Unix-like operating systems
and explained in more detail in [GitHub issue #8][issue8]. On these
platforms, if all you did was install MPh, starting the client in
stand-alone mode will raise a `java.lang.UnsatisfiedLinkError`
because required external libraries cannot be found. You would have
to add the full paths of shared-library folders to an environment
variable named `LD_LIBRARY_PATH` on Linux and `DYLD_LIBRARY_PATH` on
macOS.

For example, for an installation of Comsol 5.6 on Ubuntu Linux, you
would add the following lines at the end of the shell configuration
file `.bashrc`:
```shell
# Help MPh find Comsol's shared libraries.
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH\
:/usr/local/comsol56/multiphysics/lib/glnxa64\
:/usr/local/comsol56/multiphysics/lib/glnxa64/gcc\
:/usr/local/comsol56/multiphysics/ext/graphicsmagick/glnxa64\
:/usr/local/comsol56/multiphysics/ext/cadimport/glnxa64
```

On macOS, the root folder is `/Applications/COMSOL56/Multiphysics`.
The folder names in this example depend on the installed Comsol version
and will have to be adapted accordingly.

Requiring this variable to be set correctly limits the possibility of
selecting a specific Comsol version from within MPh, as adding multiple
installations to that search path will lead to name collisions. One
could work around the issue by wrapping a Python program that uses MPh
in a shell script that sets the environment variable only for that one
process. Or have the Python program start the Comsol session in a
subprocess. However, none of this is ideal. Starting the client should
work without any of these detours.

The function `mph.start()` function exists to navigate these platform
differences. On Windows, it starts a stand-alone client in order to
profit from the better start-up performance. On Linux and macOS, it
creates a local session in client–server mode so that no shell
configuration is required up front. This behavior is reflected in the
configuration option "session", accessible via `mph.option()`, which is
set to "platform-dependent" by default. It could also be set to
"stand-alone" or "client-server" before calling `mph.start()` in order
to override the default behavior.


[repo]:   https://github.com/john-hennig/mph
[tests]:  https://github.com/John-Hennig/mph/tree/master/tests
[jpype]:  https://jpype.readthedocs.io
[jnius]:  https://pyjnius.readthedocs.io
[pytest]: https://docs.pytest.org
[japi]:   https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[issues]: https://github.com/John-Hennig/MPh/issues
[issue8]: https://github.com/John-Hennig/MPh/issues/8
