"""
Tests if `KeyboardInterrupt` exception are properly handled.

This test currently fails. That is, trying to interrupt an ongoing
operation of the Comsol client crashes out of the Python session
instead of allowing further code execution or a return to the
interactive prompt.

The script does not depend on MPh, but starts the Comsol client
directly via the Java bridge JPype. Paths to the Comsol installation
are hard-coded for a Windows installation of Comsol 5.5. Other versions
or install locations can be tested by editing the assignment to the
`root` variable. On Linux, 'win64' has to be replaced by 'glnxa64',
and on macOS by 'maci64'.
"""

import jpype
import jpype.imports
from time import sleep
from pathlib import Path

print(f'Starting Comsol\'s Java VM via JPype {jpype.__version__}.')
root = Path(r'C:\Program Files\COMSOL\COMSOL55\Multiphysics')
jvm  = root/'java'/'win64'/'jre'/'bin'/'server'/'jvm.dll'
jpype.startJVM(str(jvm), classpath=str(root/'plugins'/'*'))

print('Starting stand-alone Comsol client.')
from com.comsol.model.util import ModelUtil as client
client.initStandalone(False)
client.loadPreferences()

print('Press Ctrl+C within the next 10 seconds.')
try:
    sleep(10)
except KeyboardInterrupt:
    print('Test passed.')
finally:
    print('Finally block executed.')

print('All went well if you see this line in the output.')
