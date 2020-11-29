"""
Tests Comsol client behavior on Linux or Windows using JPype only.

The script demonstrates two issues that are currently unresolved.

On Linux, the client can only be "initialized" if we do
```console
    export LD_LIBRARY_PATH=/usr/local/comsol55/multiphysics/lib/glnxa64
```
in the Linux shell first. Otherwise the line
```python
    client.initStandalone(False)
```
throws a `java.lang.UnsatisfiedLinkError` because one of the external
dynamic libraries (*.so) from the above directory cannot be found.
That information should, however, be provided from within the Python
code.

On Windows, the Java Virtual Machine often does not shut down, or at
least not in a timely manner. If we run this script as is (with
Comsol 5.5 or 5.6, JPype 1.1.2), the shutdown takes (almost exactly)
60 seconds. If we only start the client, but never load a model,
things are fine. This can be tested by passing `skip_load` as a
command-line argument. In other scenarios (not tested by this script),
where the client actually did something useful in between, such as
evaluating a solution, the shutdown seems to never happen. The only
work-around, at this point, is to forcefully stop the Java VM. Pass
`force_exit` to see this in action.
"""

import platform
import os
import sys
from pathlib import Path
from time import perf_counter as now


system = platform.system()
print(f'Operating system: {system}')
if system == 'Windows':
    main = Path(r'C:\Program Files\COMSOL\COMSOL55\Multiphysics')
    jre  = main / 'java' / 'win64' / 'jre' / 'bin'
    jvm  = jre / 'server' / 'jvm.dll'
    api  = main / 'plugins' / '*'
    lib = main / 'lib' / 'win64'
elif system == 'Linux':
    main = Path('/usr/local/comsol55/multiphysics')
    jre  = main / 'java' / 'glnxa64' / 'jre'
    jvm  = jre / 'lib' / 'amd64' / 'server' / 'libjvm.so'
    api  = main / 'plugins' / '*'
    lib = main / 'lib' / 'glnxa64'
else:
    raise NotImplementedError('Unsupported operating system.')

if jvm.is_file():
    print(f'JVM path: {jvm}.')
else:
    print('JVM does not exist.')

print('Setting environment variables.')
os.environ['PATH'] = str(jre)
if system == 'Linux':
    os.environ['LD_LIBRARY_PATH'] = str(lib)
    # Only really works if we do:
    #     export LD_LIBRARY_PATH=/usr/local/comsol55/multiphysics/lib/glnxa64
    # in the Linux shell first.
    # Otherwise loaded libraries don't find other libraries they depend on.

print('Limiting number of cores to 1.')
os.environ['COMSOL_NUM_THREADS'] = '1'

import jpype
import jpype.imports
print(f'JPype version: {jpype.__version__}')

print('Starting Comsol\'s Java VM.')
t0 = now()
jpype.startJVM(str(jvm), f'-Djava.library.path={lib}',
               classpath=str(api), convertStrings=False)
print(f'JVM started in {now()-t0:.3f} seconds.')

cores = jpype.java.lang.System.getenv('COMSOL_NUM_THREADS')
print(f'Number of cores is set to {cores}.')

path = jpype.java.lang.System.getProperty('java.library.path')
if path:
    folders = path.split(os.pathsep)
    print('Java library search path is:')
    for folder in folders:
        print(f'    {folder}')

path = jpype.java.lang.System.getenv('PATH')
if path:
    folders = path.split(os.pathsep)
    print('System binary search path is:')
    for folder in folders:
        print(f'    {folder}')

if system == 'Linux':
    path = jpype.java.lang.System.getenv('LD_LIBRARY_PATH')
    if path:
        folders = path.split(os.pathsep)
        print('System library search path is:')
        for folder in folders:
            print(f'    {folder}')

print('Importing Comsol API.')
from com.comsol.model.util import ModelUtil as client
print('Comsol API imported.')

print('Initializing stand-alone client.')
t0 = now()
client.initStandalone(False)
client.loadPreferences()
print(f'Client initialized after {now()-t0:.3f} seconds.')

if 'skip_load' not in sys.argv[1:]:
    print('Loading Comsol model.')
    t0 = now()
    tag = client.uniquetag('model')
    model = client.load(tag, 'blank.mph')
    print(f'Loading model took {now()-t0:.3f} seconds.')

# Possibly crash out of JVM.
if 'force_exit' in sys.argv[1:]:
    print('Exiting JVM.')
    jpype.java.lang.Runtime.getRuntime().exit(0)

# Calling `.halt(0)` would be even more forceful.
# Another thing I've tried to exit more gracefully, but to no avail:
#     from com import comsol
#     current_thread = jpype.java.lang.Thread.currentThread()
#     comsol.systemutils.SystemUtil.setMainThread(current_thread)
#     jpype.java.lang.Runtime.getRuntime().runFinalization()

# This won't be reached if "force_exit" is passed.
print('Shutting down JVM.')
t0 = now()
jpype.shutdownJVM()
print(f'JVM has shut down in {now()-t0:.3f} seconds.')
