"""
Discovers Comsol installations on the local machine.

This is a helper module that is not part of the public API. It
retrieves information about installed Comsol versions, i.e. available
simulation back-ends, and locates the installation folder.

The discovery mechanism currently only works on Windows, as it relies
on the Registry to provide that information.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import platform                        # platform information
import winreg                          # Windows registry
import re                              # regular expressions
from subprocess import run, PIPE       # external processes
from collections import namedtuple     # named tuples
from functools import lru_cache        # least-recently-used cache
from numpy import array                # numerical arrays
from pathlib import Path               # file paths
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # package-wide event logger


########################################
# Functions                            #
########################################

@lru_cache(maxsize=1)
def versions():
    """
    Returns version information of available Comsol installations.

    Version information is returned as a list of named tuples
    containing the major, minor and patch version numbers, the
    build number, and the installation folder.

    Currently, this has only been implemented for the Windows
    operating system. On other platforms, such as Linux and MacOS,
    the code here would have to be amended, namely because
    locating installed software is system-specific.

    Raises `RuntimeError` if no Comsol installation was found.
    Raises `NotImplementedError` on operating systems other than
    Windows.
    """

    # Define data type describing a back-end installation.
    Version = namedtuple('version',
                        ('major', 'minor', 'patch', 'build', 'folder'))

    # Bail out if not on the Windows platform.
    system = platform.system()
    if system != 'Windows':
        error = (f'Unsupported operating system "{system}".'
                 f'This library is (currently) Windows-only.')
        logger.error(error)
        raise NotImplementedError(error)

    # Open main Comsol registry node.
    path_main = r'SOFTWARE\Comsol'
    try:
        main = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path_main,
                              access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        error = 'Did not find Comsol registry entry.'
        logger.error(error)
        raise OSError(error) from None

    # Parse sub-nodes to get list of installed Comsol versions.
    versions = {}
    index = 0
    while True:

        # Get name of next node. Exit loop if list exhausted.
        try:
            name = winreg.EnumKey(main, index)
            index += 1
        except OSError:
            break

        # Ignore nodes that don't follow naming pattern.
        if not re.match(r'(?i)Comsol\d+[a-z]?', name):
            logger.debug(f'Ignoring registry node "{name}".')
            continue

        # Open the sub-node.
        path_node = path_main + '\\' + name
        logger.debug(f'Checking registry node "{path_node}".')
        try:
            node = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path_node,
                      access=winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
        except FileNotFoundError:
            error = f'Could not open registry node "{name}".'
            logger.error(error)
            continue

        # Get installation folder from corresponding key.
        key = 'COMSOLROOT'
        try:
            value = winreg.QueryValueEx(node, key)
        except FileNotFoundError:
            error = f'Key "{key}" missing in node "{name}".'
            logger.error(error)
            continue
        folder = Path(value[0])
        logger.debug(f'Checking installation folder "{folder}".')

        # Check that server executable exists.
        path = folder / 'bin' / architecture() / 'comsolmphserver.exe'
        if not path.exists():
            error = 'Did not find Comsol server executable.'
            logger.error(error)
            continue

        # Query the Comsol server's version information.
        flags = 0x08000000 if platform.system() == 'Windows' else 0
        command = [str(path), '--version']
        process = run(command, stdout=PIPE, creationflags=flags)
        if process.returncode != 0:
            error = 'Querying version information failed.'
            logger.error(error)
        answer = process.stdout.decode('ascii', errors='ignore').strip()
        logger.debug(f'Reported version info is "{answer}".')

        # Parse out the actual version number.
        match = re.match(r'(?i)Comsol.*?(\d+(?:\.\d+)*)', answer)
        if not match:
            error = f'Unexpected answer "{answer}" to version query.'
            logger.error(error)
            continue
        number = match.group(1)

        # Break the version number down into parts.
        parts = number.split('.')
        if len(parts) > 4:
            error = f'Reported version "{number}" has more than four parts.'
            logger.error(error)
            continue
        try:
            parts = [int(part) for part in parts]
        except ValueError:
            error = f'Not all parts of version "{number}" are numbers.'
            logger.error(error)
            continue
        parts = parts + [0]*(4-len(parts))
        (major, minor, patch, build) = parts

        # Assign a standardized name to this version.
        name = f'{major}.{minor}'
        if patch > 0:
            name += chr(ord('a') + patch - 1)
        logger.debug(f'Assigned name "{name}" to this installation.')

        # Check that Java virtual machine exists.
        java = folder / 'java' / architecture() / 'jre' / 'bin'
        jvm  = java / 'server' / 'jvm.dll'
        if not jvm.exists():
            error = 'Did not find Java virtual machine.'
            logger.error(error)
            continue

        # Check that Java API folder exists.
        path = folder / 'plugins'
        if not path.exists():
            error = 'Did not find Comsol API plugins.'
            logger.error(error)
            continue

        # Add to list of installed versions.
        if name in versions:
            logger.warning(f'Ignoring duplicate of Comsol version {name}.')
        else:
            versions[name] = Version(major, minor, patch, build, folder)

    # Report error if no Comsol installation was found.
    if not versions:
        error = 'Could not locate any Comsol installation.'
        logger.error(error)
        raise RuntimeError(error)

    # Sort versions by name.
    versions = dict(sorted(versions.items()))

    # Return list of installed versions.
    return versions


def folder(version=None):
    """
    Returns the path to the Comsol installation folder.

    A specific Comsol `version` can be named, if several are
    installed, for example `version='5.3a'`. Otherwise the latest
    version is used.

    Relies on `versions()` to discover installations.

    Raises `ValueError` if the requested version is not installed.
    """
    if version is not None:
        if version not in versions():
            error = f'Version {version} is not installed.'
            logger.error(error)
            raise ValueError(error)
        return versions()[version].folder
    else:
        last = list(versions().keys())[-1]
        return versions()[last].folder


@lru_cache(maxsize=1)
def architecture():
    """
    Returns the name of the "architecture" folder inside the
    Comsol root folder.

    That folder name is platform-dependent:
    • `win64` on Windows
    • `glnxa64` on Linux
    • `maci64` on Mac OS

    These are all builds for 64-bit CPU architectures. As Comsol no
    longer supports 32-bit architectures, neither does this library.

    Raises `OSError` if the operating system the application runs on
    is not supported. Currently, these are all operating systems apart
    from Windows.
    """
    system = platform.system()
    if system == 'Windows':
        return 'win64'
    elif system == 'Linux':
        return 'glnxa64'
    elif system == 'Darwin':
        return 'maci64'
    else:
        error = f'Operating system "{system}" not supported.'
        logger.error(error)
        raise OSError(error)


def inspect(java):
    """
    Inspects a Java object representing a Comsol model feature.

    This is basically a "pretty-fied" version of the output from the
    standard `dir` command. It displays (prints to the console) the
    methods of a model node, given as a `java` object as provided by
    the Comsol API, as well as the node's "property" names and values,
    if any are defined.

    The node's name, tag, and documentation reference marker are
    listed first. These access methods and a few others, which are
    common to all objects, are suppressed in the method list further
    down, for the sake of clarity.
    """

    # Display general information about the feature.
    print(f'name:    {java.name()}')
    print(f'tag:     {java.tag()}')
    try:
        print(f'type:    {java.getType()}')
    except AttributeError:
        pass
    print(f'display: {java.getDisplayString()}')
    print(f'doc:     {java.docMarker()}')

    # Display comments and notify if feature is deactivated or has warnings.
    comments = str(java.comments())
    if comments:
        print(f'comment: {comments}')
    if not java.isActive():
        print('This feature is currently deactivated.')
    try:
        if java.hasWarning():
            print('This feature has warnings.')
    except AttributeError:
        pass

    # Introspect the feature's attributes.
    attributes = [attribute for attribute in dir(java)]

    # Display properties if any are defined.
    if 'properties' in attributes:
        print('properties:')
        names = [str(property) for property in java.properties()]
        for name in names:
            dtype = str(java.getValueType(name))
            if dtype == 'Int':
                value = int(java.getInt(name))
            elif dtype == 'IntArray':
                value = array(java.getIntArray(name))
            elif dtype == 'IntMatrix':
                value = array([line for line in java.getIntMatrix(name)])
            elif dtype == 'Boolean':
                value = java.getBoolean(name)
            elif dtype == 'BooleanArray':
                value = array(java.getBooleanArray(name))
            elif dtype == 'BooleanMatrix':
                value = array([line for line in java.getBooleanMatrix(name)])
            elif dtype == 'Double':
                value = java.getDouble(name)
            elif dtype == 'DoubleArray':
                value = array(java.getDoubleArray(name))
            elif dtype == 'DoubleMatrix':
                value = array([line for line in java.getDoubleMatrix(name)])
            elif dtype == 'String':
                value = str(java.getString(name))
            elif dtype == 'StringArray':
                value = [str(string) for string in java.getStringArray(name)]
            elif dtype == 'StringMatrix':
                value = [[str(string) for string in line]
                         for line in java.getStringMatrix(name)]
            else:
                value = '[?]'
            print(f'  {name}: {value}')

    # Define a list of common methods to be suppressed in the output.
    suppress = ['name', 'label', 'tag', 'getType', 'getDisplayString',
                'docMarker', 'help', 'comments', 'toString', 'icon',
                'properties', 'hasProperty', 'set',
                'getEntryKeys', 'getEntryKeyIndex', 'getValueType',
                'getInt',     'getIntArray',     'getIntMatrix',
                'getBoolean', 'getBooleanArray', 'getBooleanMatrix',
                'getDouble',  'getDoubleArray',  'getDoubleMatrix',
                'getString',  'getStringArray',  'getStringMatrix',
                'version', 'author', 'resetAuthor', 'lastModifiedBy',
                'dateCreated', 'dateModified', 'timeCreated', 'timeModified',
                'active', 'isActive', 'isactive', 'hasWarning',
                'class_', 'getClass', 'hashCode',
                'notify', 'notifyAll', 'wait']

    # Display the feature's methods.
    print('methods:')
    for name in attributes:
        if name.startswith('_') or name in suppress:
            continue
        print(f'  {name}')
