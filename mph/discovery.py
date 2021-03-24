"""
Discovers Comsol installations.

This is an internal helper module that is not part of the public API.
It retrieves information about installed Comsol versions, i.e.
available simulation back-ends, and locates the installation folders.

On Windows, the discovery mechanism relies on the Registry to provide
information about install locations. On Linux and macOS, Comsol is
expected to be installed at its respective default location.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import platform                        # platform information
import re                              # regular expressions
from subprocess import run, PIPE       # external processes
from functools import lru_cache        # least-recently-used cache
from pathlib import Path               # file paths
from sys import version_info           # Python version
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


########################################
# Version information                  #
########################################

def parse(version):
    """
    Parses version information as returned by Comsol executable.

    Returns `(name, major, minor, patch, build)` where `name` is a
    string and the rest are numbers. The name is a short-hand based
    on the major, minor, and patch version numbers, e.g. `'5.3a'`.

    Raises `ValueError` if the input string deviates from the expected
    format, i.e., the format in which the Comsol executable returns
    version information.
    """

    # Separate version number from preceding program name.
    match = re.match(r'(?i)Comsol.*?(\d+(?:\.\d+)*)', version)
    if not match:
        raise ValueError(f'Version info "{version}" has invalid format.')
    number = match.group(1)

    # Break the version number down into parts.
    parts = number.split('.')
    if len(parts) > 4:
        raise ValueError(f'Version number "{number}" has too many parts.')
    try:
        parts = [int(part) for part in parts]
    except ValueError:
        error = f'Not all parts of version "{number}" are numbers.'
        raise ValueError(error) from None
    parts = parts + [0]*(4-len(parts))
    (major, minor, patch, build) = parts

    # Assign a short-hand name to this version.
    name = f'{major}.{minor}'
    if patch > 0:
        name += chr(ord('a') + patch - 1)

    # Return version details.
    return (name, major, minor, patch, build)


########################################
# Discovery mechanism                  #
########################################

def search_Windows():
    """Searches for Comsol installations on a Windows system."""

    # Collect all information in a list.
    backends = []

    # Import Windows-specific library for registry access.
    import winreg

    # Open main Comsol registry node.
    main_path = r'SOFTWARE\Comsol'
    try:
        main_node = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, main_path)
    except FileNotFoundError:
        error = 'Did not find Comsol registry entry.'
        logger.critical(error)
        raise LookupError(error) from None

    # Parse child nodes to get list of Comsol installations.
    index = 0
    while True:

        # Get name of next node. Exit loop when list exhausted.
        try:
            node_name = winreg.EnumKey(main_node, index)
            index += 1
        except OSError:
            break

        # Ignore nodes that don't follow naming pattern.
        if not re.match(r'(?i)Comsol\d+[a-z]?', node_name):
            logger.debug(f'Ignoring registry node "{node_name}".')
            continue

        # Open the child node.
        node_path = main_path + '\\' + node_name
        logger.debug(f'Checking registry node "{node_path}".')
        try:
            node = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, node_path)
        except FileNotFoundError:
            logger.debug(f'Could not open registry node "{node_name}".')
            continue

        # Get installation folder from corresponding key.
        key = 'COMSOLROOT'
        try:
            value = winreg.QueryValueEx(node, key)
        except FileNotFoundError:
            logger.debug(f'Key "{key}" missing in node "{node_name}".')
            continue
        root = Path(value[0])
        logger.debug(f'Checking installation folder "{root}".')

        # Check that Comsol server executable exists.
        server = root/'bin'/'win64'/'comsolmphserver.exe'
        if not server.exists():
            logger.debug('Did not find Comsol server executable.')
            continue

        # Get version information from Comsol server.
        command = [server, '--version']
        if version_info < (3, 8):
            command[0] = str(command[0])
        process = run(command, stdout=PIPE, creationflags=0x08000000)
        if process.returncode != 0:
            logger.debug('Querying version information failed.')
            continue
        version = process.stdout.decode('ascii', errors='ignore').strip()
        logger.debug(f'Reported version info is "{version}".')

        # Parse version information.
        try:
            (name, major, minor, patch, build) = parse(version)
        except ValueError as error:
            logger.debug(error)
            continue
        logger.debug(f'Assigned name "{name}" to this installation.')

        # Ignore installation if version name is a duplicate.
        if name in (backend['name'] for backend in backends):
            logger.warning(f'Ignoring duplicate of Comsol version {name}.')
            continue

        # Verify existence of required files and folders.
        jre = root/'java'/'win64'/'jre'
        if not jre.exists():
            logger.debug('Did not find Java run-time environment.')
            continue
        java = jre/'bin'
        if not java.exists():
            logger.debug('Did not find Java run-time binaries.')
            continue
        jvm = java/'server'/'jvm.dll'
        if not jvm.exists():
            logger.debug('Did not find Java virtual machine.')
            continue
        api = root/'plugins'
        if not api.exists():
            logger.debug('Did not find Comsol Java API plug-ins.')
            continue
        lib = root/'lib'/'win64'
        if not lib.exists():
            logger.debug('Did not find Comsol shared libraries.')
            continue

        # Collect all information in a dictionary and add it to the list.
        backends.append({
            'name':   name,
            'major':  major,
            'minor':  minor,
            'patch':  patch,
            'build':  build,
            'root':   root,
            'jvm':    jvm,
            'server': [server],
        })

    # Return list with information about all installed Comsol back-ends.
    return backends


def search_Linux():
    """Searches for Comsol installations on a Linux system."""

    # Collect all information in a list.
    backends = []

    # Loop over Comsol folders in /usr/local.
    folders = [item for item in Path('/usr/local').glob('comsol*')
               if item.is_dir()]
    for folder in folders:

        # Root folder is the sub-directory "multiphysics".
        root = folder/'multiphysics'
        if not root.is_dir():
            logger.debug(f'No folder "multiphysics" in "{folder.name}".')
            continue
        logger.debug(f'Checking installation folder "{root}".')

        # Check that Comsol executable exists.
        comsol = root/'bin'/'glnxa64'/'comsol'
        if not comsol.exists():
            logger.debug('Did not find Comsol executable.')
            continue

        # Get version information from Comsol server.
        process = run([comsol, 'server', '--version'], stdout=PIPE)
        if process.returncode != 0:
            logger.debug('Querying version information failed.')
            continue
        version = process.stdout.decode('ascii', errors='ignore').strip()
        logger.debug(f'Reported version info is "{version}".')

        # Parse version information.
        try:
            (name, major, minor, patch, build) = parse(version)
        except ValueError as error:
            logger.debug(error)
            continue
        logger.debug(f'Assigned name "{name}" to this installation.')

        # Ignore installation if version name is a duplicate.
        if name in (backend['name'] for backend in backends):
            logger.warning(f'Ignoring duplicate of Comsol version {name}.')
            continue

        # Verify existence of required files and folders.
        jre = root/'java'/'glnxa64'/'jre'
        if not jre.exists():
            logger.debug('Did not find Java run-time environment.')
            continue
        java = jre/'bin'
        if not java.exists():
            logger.debug('Did not find Java run-time binaries.')
            continue
        jvm = jre/'lib'/'amd64'/'server'/'libjvm.so'
        if not jvm.exists():
            logger.debug('Did not find Java virtual machine.')
            continue
        api = root/'plugins'
        if not api.exists():
            logger.debug('Did not find Comsol Java API plug-ins.')
            continue
        lib = root/'lib'/'glnxa64'
        if not lib.exists():
            logger.debug('Did not find Comsol shared libraries.')
            continue
        gra = root/'ext'/'graphicsmagick'/'glnxa64'
        if not gra.exists():
            logger.debug('Did not find graphics libraries.')
            continue

        # Collect all information in a dictionary and add it to the list.
        backends.append({
            'name':   name,
            'major':  major,
            'minor':  minor,
            'patch':  patch,
            'build':  build,
            'root':   root,
            'jvm':    jvm,
            'server': [comsol, 'mphserver'],
        })

    # Return list with information about all installed Comsol back-ends.
    return backends


def search_macOS():
    """Searches for Comsol installations on a macOS system."""

    # Collect all information in a list.
    backends = []

    # Loop over Comsol folders in /Applications.
    folders = [item for item in Path('/Applications').glob('COMSOL*')
               if item.is_dir()]
    for folder in folders:

        # Root folder is the sub-directory "Multiphysics".
        root = folder/'Multiphysics'
        if not root.is_dir():
            logger.debug(f'No folder "Multiphysics" in "{folder.name}".')
            continue
        logger.debug(f'Checking installation folder "{root}".')

        # Check that Comsol executable exists.
        comsol = root/'bin'/'maci64'/'comsol'
        if not comsol.exists():
            logger.debug('Did not find Comsol executable.')
            continue

        # Get version information from Comsol server.
        process = run([comsol, 'server', '--version'], stdout=PIPE)
        if process.returncode != 0:
            logger.debug('Querying version information failed.')
            continue
        version = process.stdout.decode('ascii', errors='ignore').strip()
        logger.debug(f'Reported version info is "{version}".')

        # Parse version information.
        try:
            (name, major, minor, patch, build) = parse(version)
        except ValueError as error:
            logger.debug(error)
            continue
        logger.debug(f'Assigned name "{name}" to this installation.')

        # Ignore installation if version name is a duplicate.
        if name in (backend['name'] for backend in backends):
            logger.warning(f'Ignoring duplicate of Comsol version {name}.')
            continue

        # Verify existence of required files and folders.
        jre = root/'java'/'maci64'/'jre'
        if not jre.exists():
            logger.debug('Did not find Java run-time environment.')
            continue
        java = jre/'Contents'/'Home'/'bin'
        if not java.exists():
            logger.debug('Did not find Java run-time binaries.')
            continue
        jvm = jre/'Contents'/'Home'/'lib'/'server'/'libjvm.dylib'
        if not jvm.exists():
            jvm = jre/'Contents'/'Home'/'lib'/'server'/'libjvm.so'
            if not jvm.exists():
                logger.debug('Did not find Java virtual machine.')
                continue
        api = root/'plugins'
        if not api.exists():
            logger.debug('Did not find Comsol Java API plug-ins.')
            continue
        lib = root/'lib'/'maci64'
        if not lib.exists():
            logger.debug('Did not find Comsol shared libraries.')
            continue
        gra = root/'ext'/'graphicsmagick'/'maci64'
        if not gra.exists():
            logger.debug('Did not find graphics libraries.')
            continue

        # Collect all information in a dictionary and add it to the list.
        backends.append({
            'name':   name,
            'major':  major,
            'minor':  minor,
            'patch':  patch,
            'build':  build,
            'root':   root,
            'jvm':    jvm,
            'server': [comsol, 'mphserver'],
        })

    # Return list with information about all installed Comsol back-ends.
    return backends


@lru_cache(maxsize=1)
def search_system():
    """Searches the system for Comsol installations."""
    system = platform.system()
    if system == 'Windows':
        return search_Windows()
    elif system == 'Linux':
        return search_Linux()
    elif system == 'Darwin':
        return search_macOS()
    else:
        error = f'Unsupported operating system "{system}".'
        logger.critical(error)
        raise NotImplementedError(error)


########################################
# Back-end selection                   #
########################################

def backend(version=None):
    """
    Returns information about the Comsol back-end.

    A specific Comsol `version` can be selected by name if several
    are installed, for example `version='5.3a'`. Otherwise the latest
    version is used.
    """
    backends = search_system()
    if not backends:
        error = 'Could not locate any Comsol installation.'
        logger.critical(error)
        raise RuntimeError(error)
    if version is None:
        numbers = [(backend['major'], backend['minor'], backend['patch'],
                   backend['build']) for backend in backends]
        return backends[numbers.index(max(numbers))]
    else:
        names = [backend['name'] for backend in backends]
        return backends[names.index(version)]
