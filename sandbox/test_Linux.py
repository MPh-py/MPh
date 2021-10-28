"""
Tests running a stand-alone Comsol client on Linux.

The script does not depend on MPh, but starts the Comsol client
directly via JPype. Paths to the Comsol installation are hard-coded
for an installation of Comsol 5.6 at the default location. Other
versions can be tested by editing the assignment to `root`.

Even though this script sets up all environment variables just like
the Comsol documentation suggests for Java development with the
Eclipse IDE (on pages 23 and 916 in the Programming Reference Manual
of Comsol 5.6), it still fails to work unless the user sets
`LD_LIBRARY_PATH` in the shell *before* starting the script:
```shell
export LD_LIBRARY_PATH=\
/usr/local/comsol56/multiphysics/lib/glnxa64:\
/usr/local/comsol56/multiphysics/ext/graphicsmagick/glnxa64:\
/usr/local/comsol56/multiphysics/ext/cadimport/glnxa64
```

It is odd that this is necessary because, as this script demonstrates,
the Java VM is well aware of the above environment variable even if
the user does not set it beforehand. It is also not Java that has
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


@atexit.register
def exit_JVM():
    if jpype.isJVMStarted():
        jpype.java.lang.Runtime.getRuntime().exit(0)


print('Setting environment variables.')
root = '/usr/local/comsol56/multiphysics'
lib  = root + '/lib/glnxa64'
gcc  = root + '/lib/glnxa64/gcc'
mgk  = root + '/ext/graphicsmagick/glnxa64'
cad  = root + '/ext/cadimport/glnxa64'
pre  = root + '/java/glnxa64/jre/lib/amd64/libjsig.so'
var  = 'LD_LIBRARY_PATH'
path = os.environ[var].split(os.pathsep) if var in os.environ else []
os.environ[var] = os.pathsep.join(path + [lib, gcc, mgk, cad])
vars = ('MAGICK_CONFIGURE_PATH',
        'MAGICK_CODER_MODULE_PATH',
        'MAGICK_FILTER_MODULE_PATH')
for var in vars:
    os.environ[var] = mgk
os.environ['LD_PRELOAD'] = pre
os.environ['LC_NUMERIC'] = os.environ['LC_ALL'] = 'C'

print(f"Starting Comsol's Java VM via JPype {jpype.__version__}.")
jvm = root + '/java/glnxa64/jre/lib/amd64/server/libjvm.so'
jpype.startJVM(jvm, classpath=root + '/plugins/*')

print('Inspecting environment from the Java side.')
path = jpype.java.lang.System.getProperty('java.library.path') or ''
print('• Java library search:')
for folder in path.split(os.pathsep):
    print(f'  {folder}')
path = jpype.java.lang.System.getenv('PATH') or ''
print('• System binary search:')
for folder in path.split(os.pathsep):
    print(f'  {folder}')
path = jpype.java.lang.System.getenv('LD_LIBRARY_PATH') or ''
print('• System library search:')
for folder in path.split(os.pathsep):
    print(f'  {folder}')

print('Starting stand-alone Comsol client.')
from com.comsol.model.util import ModelUtil as client
client.initStandalone(False)
client.loadPreferences()

print('Testing if Comsol can load shared libraries.')
from com.comsol.nativejni import FlNativeUtil
FlNativeUtil.ensureLibIsLoaded()

print('Loading Comsol model.')
model = client.load('model1', '../demos/capacitor.mph')

print('Solving study "std1".')
model.study('std1').run()

print('Exporting image.')
model.result().export('img1').run()
