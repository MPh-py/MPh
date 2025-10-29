# Limitations

## Java bridge

MPh is built on top of the Python-to-Java bridge [JPype]. It is JPype that
allows us to look at Comsol's [Programming Manual] or its [API reference] and
run the same commands from Python.

Unfortunately, the Comsol API does not support running more than one client at
a time, i.e. within the same Java program. Meanwhile, JPype cannot manage more
than one Java virtual machine within the same Python process. If it could, it
would be easy to work around Comsol's limitation. (There is an alternative Java
bridge, [pyJNIus], which is not limited to one virtual machine, but then fails
in another regard: A number of Java methods exposed by Comsol are inexplicably
missing from the Python encapsulation.)

Therefore, if several simulations are to be run in parallel, distributed over
independent processor cores in an effort to achieve maximum speed-up of a
parameter sweep, they have to be started as separate Python subprocesses. Refer
to section ["Multiple processes"](demonstrations.md#multiple-processes) for a
demonstration.

Additionally, there are some known, but unresolved issues with JPype's shutdown
of the Java virtual machine. Notably, pressing <kbd>Ctrl+C</kbd> to interrupt
an ongoing operation will usually crash the Python session. So do not rely on
catching [`KeyboardInterrupt`](#KeyboardInterrupt) exceptions in application
code.


## Platform differences

Comsol offers two distinct ways to run a simulation session on the local
machine. We can either start a "stand-alone" client, which does not require a
separate Comsol server. Or we first start a server and then have a "thin"
client connect to it via a loop-back network socket. The first approach is more
lightweight and perhaps more robust, as it keeps everything inside the same
process. The second approach is slower to start up and relies on the
inter-process communication, but would also work across the network, i.e., for
remote sessions where the client runs locally and delegates the heavy lifting
to a server running on another machine. If we instantiate the
[`Client`](#Client) class without providing a value for the network port, it
will create a stand-alone client. Otherwise it will run as a thin client in
client–server mode.

On Linux and macOS, however, the stand-alone mode does not work out of the box.
This is due to a limitation of Unix-like operating systems and explained in
more detail in [GitHub issue #8]. On these platforms, if all you did was
install MPh, starting the client in stand-alone mode will raise a
`java.lang.UnsatisfiedLinkError` because required external libraries cannot be
found. You would have to add the full paths of certain shared-library folders
to an environment variable named `LD_LIBRARY_PATH` on Linux and
`DYLD_LIBRARY_PATH` on macOS.

For example, for an installation of Comsol 6.3 on Linux, you would add the
following lines at the end of the shell configuration file `.bashrc`.
```shell
# Help MPh find Comsol's shared libraries in stand-alone mode.
ComsolDir=/usr/local/comsol63/multiphysics
export LD_LIBRARY_PATH=\
$ComsolDir/lib/glnxa64:\
$ComsolDir/lib/glnxa64/gcc:\
$ComsolDir/ext/graphicsmagick/glnxa64:\
$ComsolDir/ext/cadimport/glnxa64:\
$LD_LIBRARY_PATH
```

On macOS, `ComsolDir` would be `/Applications/COMSOL63/Multiphysics`. The above
is [as documented for Comsol 6.3][comsol63_libpath] — make sure to consult the
corresponding documentation for your Comsol version.

Requiring the environment variable to be set correctly limits the possibility
of selecting a specific Comsol version from within MPh, as adding multiple
installations to that search path will lead to name collisions. One could work
around the issue by wrapping a Python program using MPh in a shell script that
sets the environment variable before starting the Python process. That's
effectively what Comsol itself does to launch its own GUI (Comsol Desktop) on
one of these platforms. Or we could have a Python program that sets the
environment variable and then runs MPh in a second Python subprocess. Clearly,
none of this is ideal. Starting the client should work without any of these
detours.

Therefore, the function [`mph.start()`](#start) defaults to operating in
client–server mode. This is reflected in the configuration option `'session'`,
accessible via [`mph.option()`](#option), being set to `'client-server'` by
default. Alternatively, it could be set to `'stand-alone'` to unconditionally
request a stand-alone client. Or to `'platform-dependent'` to request a
stand-alone client on Windows, but client–server mode on other platforms.

Performance in client–server mode is noticeably worse in certain scenarios, not
just at start-up. If functions access the Comsol API frequently, such as when
navigating the model tree, perhaps even recursively as [`mph.tree()`](#tree)
does, then client–server mode can be slower by a large factor compared to a
stand-alone client. Rest assured however that simulation times are not
affected.


[JPype]:              https://github.com/jpype-project/jpype
[Programming Manual]: https://comsol.com/documentation/COMSOL_ProgrammingReferenceManual.pdf
[API reference]:      https://doc.comsol.com/6.0/doc/com.comsol.help.comsol/api
[pyJNIus]:            https://pyjnius.readthedocs.io
[GitHub issue #8]:    https://github.com/MPh-py/MPh/issues/8
[comsol63_libpath]:   https://doc.comsol.com/6.3/docserver/#!/com.comsol.help.comsol/comsol_api_intro.46.13.html
