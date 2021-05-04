# Limitations

## Java bridge

MPh is built on top of the Python-to-Java bridge [JPype][jpype]. It is
JPype that allows us to look at [Comsol's Java API][japi] and run the
same commands from Python. All credit to the JPype developers for making
this possible.

The Comsol API does not support running more than one client at a time,
i.e. within the same Java program. Meanwhile, JPype cannot manage more
than one Java virtual machine within the same Python process. If it
could, it would be easy to work around Comsol's limitation. (There is
an alternative Java bridge, [pyJNIus][jnius], which is not limited to
one virtual machine, but then fails in another regard: A number of Java
methods exposed by Comsol are inexplicably missing from the Python
encapsulation.)

Therefore, if several simulations are to be run in parallel, distributed
over independent processor cores in an effort to achieve maximum speed-up
of a parameter sweep, they have to be started as separate Python
subprocesses. Refer to section
["Multiple processes"](demonstrations.md#multiple-processes) for a
demonstration.

Additionally, there are some known, but unresolved issues with JPype's
shutdown of the Java virtual machine. Notably, pressing <kbd>Ctrl+C</kbd>
to interrupt an ongoing operation will usually crash the Python session.
So do not rely on catching [`KeyboardInterrupt`][kbint] exceptions in
application code.


## Platform differences

The [Comsol API][japi] offers two distinct ways to run a simulation
session on the local machine. One may either start a "stand-alone"
client, which does not require a Comsol server. Or one may start a
server separately and have a "thin" client connect to it via a
loop-back network socket. The first approach is more lightweight and
more reliable, as it keeps everything inside the same process. The
second approach is slower to start up and relies on the inter-process
communication to be robust, but would also work across the network,
i.e., for remote sessions where the client runs locally and delegates
the heavy lifting to a server running on another machine. If we
instantiate the [`Client`](api/mph.Client) class without providing a
value for the host address and network port, it will create a
stand-alone client. Otherwise it will run in client–server mode.

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
file `.bashrc`.
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
could work around the issue by wrapping a Python program using MPh in
a shell script that sets the environment variable only for that one
process. Or have the Python program run the Comsol session in another
Python subprocess. However, none of this is ideal. Starting the client
should work without any of these detours.

The function [`mph.start()`](api/mph.start) exists to navigate these
platform differences. On Windows, it starts a stand-alone client in
order to profit from the better start-up performance. On Linux and
macOS, it creates a local session in client–server mode so that no
shell configuration is required up front. This behavior is reflected
in the configuration option `'session'`, accessible via
[`mph.option()`](api/mph.config), which is set to `'platform-dependent'`
by default. It could also be set to `'stand-alone'` or `'client-server'`
before calling [`start()`](api/mph.start) in order to override the
default behavior.

Performance in client–server mode is noticeably worse in certain
scenarios, not just at start-up. If functions access the Java API
frequently, such as when navigating the model tree, perhaps even
recursively as [`mph.tree()`](api/mph.tree) does, then client–server
mode can be slower by a large factor compared to a stand-alone client.
Rest assured however that simulation run-times are not affected.

Conversely, setting up stand-alone mode on Linux or macOS is also
not a robust solution. Image exports, for example, are known to crash
due to some conflict with external libraries. As opposed to Windows,
where this works reliably.


[jpype]:  https://github.com/jpype-project/jpype
[japi]:  https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[jnius]:  https://pyjnius.readthedocs.io
[kbint]:  https://docs.python.org/3/library/exceptions.html#KeyboardInterrupt
[issue8]: https://github.com/MPh-py/MPh/issues/8
