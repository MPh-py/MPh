﻿"""
Discovers Comsol installations.

This is an internal helper module that is not part of the public API.
It retrieves information about installed Comsol versions, i.e.
available simulation back-ends, and locates the installation folders.

On Windows, the discovery mechanism relies on the Registry to provide
information about install locations. On Linux and macOS, Comsol is
expected to be installed at its respective default location. Though the
folder `.local` in the user's home directory is also searched to allow
symbolic linking to a custom location.

In a last step, we also run the shell command `where comsol` (on Windows)
or `which comsol` (on Linux and macOS) to find a Comsol installation
that isn't in a default location, but for which the Comsol executable
was added to the executable search path.

Note that duplicate installations will be ignored. That is, a Comsol
installation found in a later step that reports the same version as one
found in an earlier step will be ignored, regardless of install location.
"""

########################################
# Dependencies                         #
########################################
import platform                        # platform information
import subprocess                      # external processes
import re                              # regular expressions
from pathlib import Path               # file paths
from functools import lru_cache        # function cache
from logging import getLogger          # event logging

########################################
# Globals                              #
########################################
log = getLogger(__package__)           # event log
system = platform.system()             # operating system
architectures = {                      # valid system architecture names
    'Windows': ['win64'],
    'Linux':   ['glnxa64'],
    'Darwin':  ['maci64'],
}


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
# Back-end discovery                   #
########################################

def search_registry():
    """Returns Comsol executables found in the Windows Registry."""

    log.debug('Searching Windows Registry for Comsol executables.')
    executables = []

    # Import Windows-specific library for registry access.
    import winreg

    # Open main Comsol registry node.
    main_path = r'SOFTWARE\Comsol'
    try:
        main_node = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, main_path)
    except FileNotFoundError:
        log.error('Did not find Comsol registry entry.')
        return []

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
            log.debug(f'Ignoring registry node "{node_name}".')
            continue

        # Open the child node.
        node_path = main_path + '\\' + node_name
        log.debug(f'Checking registry node "{node_path}".')
        try:
            node = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, node_path)
        except FileNotFoundError:
            log.debug(f'Could not open registry node "{node_name}".')
            continue

        # Get installation folder from corresponding key.
        key = 'COMSOLROOT'
        try:
            value = winreg.QueryValueEx(node, key)
        except FileNotFoundError:
            log.debug(f'Key "{key}" missing in node "{node_name}".')
            continue
        root = Path(value[0])
        log.debug(f'Checking installation folder "{root}".')

        # Only add to list if Comsol executable exists in valid sub-folder.
        for arch in architectures[system]:
            comsol = root/'bin'/arch/'comsol.exe'
            if comsol.is_file():
                break
        else:
            log.debug('Did not find Comsol executable.')
            continue
        log.debug(f'Found Comsol executable "{comsol}".')
        executables.append(comsol)

    # Return list with file-system paths of Comsol executables.
    return executables


def search_disk():
    """Returns Comsol executables found on the file system."""

    log.debug('Searching file system for Comsol executables.')
    executables = []

    # Check system-wide and per-user application folders.
    if system == 'Linux':
        locations = [
            Path('/usr/local'),
            Path.home() / '.local',
        ]
    elif system == 'Darwin':
        locations = [
            Path('/Applications'),
            Path.home() / 'Applications',
        ]

    # Look for Comsol executables at those locations.
    folders = [item for location in locations
                    if location.is_dir()
                    for item in location.iterdir()
                    if item.is_dir() and re.match('(?i)comsol', item.name)]
    for folder in folders:
        log.debug(f'Checking candidate folder "{folder}".')

        # Root folder is usually the sub-directory "multiphysics".
        # But we also accept that this (pointless) folder is missing.
        root = folder/'multiphysics'
        if not root.is_dir():
            log.debug('No sub-folder named "multiphysics".')
            root = folder

        # Only add to list if Comsol executable exists in valid sub-folder.
        for arch in architectures[system]:
            comsol = root/'bin'/arch/'comsol'
            if comsol.is_file():
                break
        else:
            log.debug('Did not find Comsol executable.')
            continue
        log.debug(f'Found Comsol executable "{comsol}".')
        executables.append(comsol)

    # Return list with file-system paths of Comsol executables.
    return executables


def lookup_comsol():
    """Returns Comsol executable if found on the system's search path."""

    log.debug('Looking for Comsol executable on system search path.')

    # Check if Comsol executable is on search path.
    command = 'where comsol' if system == 'Windows' else 'which comsol'
    try:
        log.debug(f'Running shell command "{command}".')
        process = subprocess.run(
            command, shell=True, check=True, timeout=3,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            universal_newlines=True, encoding='UTF-8',
        )
        # `universal_newlines` instead of `text` to support Python 3.6.
    except subprocess.CalledProcessError:
        log.debug('Command exited with an error.')
        return
    except subprocess.TimeoutExpired:
        log.debug('Command execution timed out.')
        return
    response = process.stdout.strip()
    log.debug(f'Command response was "{response}".')

    # Assert that Comsol executable actually exists where reported.
    try:
        comsol = Path(response).resolve(strict=True)
    except FileNotFoundError:
        log.debug('No Comsol executable found at that path.')
        return
    log.debug(f'Found Comsol executable "{comsol}".')

    # Return executable that we found.
    return comsol


@lru_cache(maxsize=1)
def find_backends():
    """Returns the list of available Comsol back-ends."""

    log.debug('Searching system for available Comsol back-ends.')
    backends = []

    # Search system for Comsol executables.
    if system == 'Windows':
        executables = search_registry()
    elif system in ('Linux', 'Darwin'):
        executables = search_disk()
    else:
        error = f'Unsupported operating system "{system}".'
        log.error(error)
        raise NotImplementedError(error)

    # Look up `comsol` command as if run in terminal.
    comsol = lookup_comsol()
    if comsol:
        if comsol not in executables:
            executables.append(comsol)
        else:
            log.debug('Ignoring executable as it was previously found.')

    # Only accept executable when Java API was found as well.
    for comsol in executables:
        log.debug(f'Checking executable "{comsol}".')

        # The Java bridge is configured in a file named "comsol.ini".
        # That file is usually in the same folder as the Comsol executable.
        # Though on Linux and macOS, the executable may also be a script
        # that sits one folder up (for some reason).
        folders = [comsol.parent]
        for arch in architectures[system]:
            folders.append(comsol.parent/arch)
        for folder in folders:
            ini = folder/'comsol.ini'
            if ini.is_file():
                break
        else:
            log.debug(f'Did not find Java bridge configuration "{ini.name}".')
            continue
        log.debug(f'Found Java bridge configuration "{ini}".')

        # Make sure that parent folder has name of a valid architecture.
        arch = ini.parent.name
        if arch not in architectures[system]:
            log.debug('Its parent folder does not name a valid architecture.')
            continue
        log.debug(f'System architecture is "{arch}".')

        # The actual executable is the one sitting right next to "comsol.ini".
        comsol = ini.parent/comsol.name
        if not comsol.is_file():
            log.debug(f'No Comsol executable alongside "{ini.name}".')
            continue

        # On Windows, check that server executable exists in same folder.
        if system == 'Windows':
            server = ini.parent/'comsolmphserver.exe'
            if not server.exists():
                log.debug(f'No server executable alongside "{ini.name}".')
                continue
            server = [server]
        else:
            server = [comsol, 'mphserver']

        # Parse Java bridge configuration.
        with ini.open(encoding='UTF-8') as stream:
            jvm_on_next_line = False
            for line in stream:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if jvm_on_next_line:
                    jvm_path = line
                    break
                if line.startswith('-vm'):
                    jvm_on_next_line = True
            else:
                log.debug(f'Did not find Java VM path in "{ini.name}".')
                continue
        log.debug(f'Java VM at relative path "{jvm_path}".')

        # Resolve Java VM path.
        try:
            jvm = (ini.parent/jvm_path).resolve(strict=True)
        except FileNotFoundError:
            log.debug('Could not resolve relative path to Java VM.')
            continue

        # The root folder of the Comsol installation is up two levels.
        root = ini.parent.parent.parent
        log.debug(f'Root folder is "{root}".')

        # Check that folder with Comsol Java API exists.
        api = root/'plugins'
        if not api.exists():
            log.debug('Did not find Comsol Java API plug-ins in root folder.')
            continue

        # Get version information from Comsol server.
        command = server + ['--version']
        command[0] = str(command[0])   # Needed to support Python 3.6 and 3.7.
        try:
            arguments = dict(
                check=True, timeout=15,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                universal_newlines=True, encoding='ascii', errors='ignore',
            )
            # `universal_newlines` instead of `text` to support Python 3.6.
            if system == 'Windows':
                arguments['creationflags'] = 0x08000000
            process = subprocess.run(command, **arguments)
        except subprocess.CalledProcessError:
            log.debug('Querying version information failed.')
            continue
        except subprocess.TimeoutExpired:
            log.debug('Querying version information timed out.')
            continue
        version = process.stdout.strip()
        log.debug(f'Reported version information is "{version}".')

        # Parse version information.
        try:
            (name, major, minor, patch, build) = parse(version)
        except ValueError as error:
            log.debug(error)
            continue
        log.debug(f'Assigned name "{name}" to this installation.')

        # Ignore installation if version name is a duplicate.
        names = [backend['name'] for backend in backends]
        if name in names:
            log.debug(f'Ignoring duplicate of Comsol version {name}.')
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
            'server': server,
        })

    # Return list with information about all installed Comsol back-ends.
    return backends


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
    backends = find_backends()
    if not backends:
        error = 'Could not locate any Comsol installation.'
        log.error(error)
        raise RuntimeError(error)
    if version is None:
        numbers = [(backend['major'], backend['minor'], backend['patch'],
                   backend['build']) for backend in backends]
        return backends[numbers.index(max(numbers))]
    else:
        names = [backend['name'] for backend in backends]
        if version not in names:
            error = f'Could not locate Comsol {version} installation.'
            log.error(error)
            raise LookupError(error)
        return backends[names.index(version)]
