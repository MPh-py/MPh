"""Tests if the Comsol session can be safely aborted by pressing Ctrl+C."""

Comsol_root = r'C:\Program Files\COMSOL\COMSOL55\Multiphysics'

# Dependencies
import jpype
import jpype.imports
import time
from pathlib import Path

# Display version info.
print(f'JPype version: {jpype.__version__}')

# Start JVM that ships with Comsol.
main = Path(Comsol_root)
arch = 'win64'
jre  = main / 'java' / arch / 'jre' / 'bin'
jvm  = jre / 'server' / 'jvm.dll'
api  = main / 'plugins' / '*'
print(f'Path to JVM: {jvm}')
jpype.startJVM(str(jvm), classpath=str(api), convertStrings=False)
print('JVM started.')

# Start the Comsol client.
from com.comsol.model.util import ModelUtil as client
client.initStandalone(False)
print('Client started.')

# Have user trigger a keyboard interrupt.
print('Press Ctrl+C within the next 10 seconds.')
try:
    time.sleep(10)
except KeyboardInterrupt:
    print('User pressed Ctrl+C.')
finally:
    print('Finally block executed.')

# Success if the next line of code is reached.
print('All went well if you see this line in the output.')
