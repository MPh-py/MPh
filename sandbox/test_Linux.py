"""
Tests running a stand-alone Comsol client on Linux.

The script does not depend on MPh, but starts the Comsol client
directly via the Java bridge JPype. Paths to the Comsol installation
are hard-coded for an installation of Comsol 5.5 at the default
location. Other versions can be tested by editing the assignment to
the `root` variable.

Even though this script sets up all environment variables just like
the Comsol documentation suggests for Java development with the
Eclipse IDE (page 854 in Comsol 5.5's Programming Reference Manual),
it still fails to work unless the user does an explicit `export` of
the environment variable `LD_LIBRARY_PATH`, for example by adding the
following lines at the end of the shell configuration file `.bashrc`:
```shell
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:\
/usr/local/comsol55/multiphysics/lib/glnxa64:\
/usr/local/comsol55/multiphysics/ext/graphicsmagick/glnxa64
```

It is odd that this is necessary because, as this script demonstrates,
the Java VM is well aware of the above environment variable even if
the user does not explicitly `export` it. It is also not Java that has
trouble finding the external (non-Java) libraries. The issue seems to
occur because the libraries themselves, as they are being loaded
dynamically, have trouble finding each other.

Unfortunately, this means that, on Linux, MPh does not work "out of
the box", but must rely on the user to intervene, at least as far as
the stand-alone client is concerned.
"""

import jpype
import jpype.imports
import os
import atexit
from pathlib import Path


@atexit.register
def shutdown():
    """Force Java Virtual Machine to shut down at end of Python session."""
    print('Exiting JVM.')
    if jpype.isJVMStarted():
        jpype.java.lang.Runtime.getRuntime().exit(0)


print('Setting environment variables.')
root = Path('/usr/local/comsol55/multiphysics')
lib  = str(root/'lib'/'glnxa64')
gcc  = str(root/'lib'/'glnxa64'/'gcc')
ext  = str(root/'ext'/'graphicsmagick'/'glnxa64')
cad  = str(root/'ext'/'cadimport'/'glnxa64')
pre  = str(root/'java'/'glnxa64'/'jre'/'lib'/'amd64'/'libjsig.so')
var  = 'LD_LIBRARY_PATH'
if var in os.environ:
    path = os.environ[var].split(os.pathsep)
else:
    path = []
if lib not in path:
    os.environ[var] = os.pathsep.join([lib, gcc, ext, cad] + path)
vars = ('MAGICK_CONFIGURE_PATH', 'MAGICK_CODER_MODULE_PATH',
        'MAGICK_FILTER_MODULE_PATH')
for var in vars:
    os.environ[var] = ext
os.environ['LD_PRELOAD'] = pre
os.environ['LC_NUMERIC'] = os.environ['LC_ALL'] = 'C'


print(f'Starting Comsol\'s Java VM via JPype {jpype.__version__}.')
jvm = root/'java'/'glnxa64'/'jre'/'lib'/'amd64'/'server'/'libjvm.so'
jpype.startJVM(str(jvm), classpath=str(root/'plugins'/'*'))

print('Inspecting environment from the Java side.')
path = jpype.java.lang.System.getProperty('java.library.path')
print('Java library search path is:')
for folder in path.split(os.pathsep):
    print(f'    {folder}')
path = jpype.java.lang.System.getenv('PATH')
print('System binary search path is:')
for folder in path.split(os.pathsep):
    print(f'    {folder}')
path = jpype.java.lang.System.getenv('LD_LIBRARY_PATH')
print('System library search path is:')
for folder in path.split(os.pathsep):
    print(f'    {folder}')

print('Starting stand-alone Comsol client.')
from com.comsol.model.util import ModelUtil as client
client.initStandalone(False)
client.loadPreferences()

print('Testing if Comsol can load shared libraries.')
from com.comsol.nativejni import FlNativeUtil
FlNativeUtil.ensureLibIsLoaded()

print('Loading Comsol model.')
tag = client.uniquetag('model')
model = client.load(tag, '../tests/capacitor.mph')

print('Loading external image.')
tags  = [str(tag) for tag in model.func().tags()]
names = [model.func(tag).label() for tag in tags]
tag   = tags[names.index('test_function')]
model.func(tag).discardData()
model.func(tag).set('filename', '../tests/gaussian.tif')
model.func(tag).importData()

print('Solving model.')
for tag in model.study().tags():
    model.study(tag).run()
