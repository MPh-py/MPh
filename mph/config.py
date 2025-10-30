"""Manages configuration options."""

from __future__ import annotations

import os
import platform
from configparser import ConfigParser
from pathlib import Path
from logging import getLogger

from typing import overload, TypedDict


class Options(TypedDict):
    session:  str
    caching:  bool
    classkit: bool


options = {
    'session':  'client-server',
    'caching':  False,
    'classkit': False,
}
"""Default values for configuration options."""

system = platform.system()
log    = getLogger(__package__)


##########
# Access #
##########

@overload
def option(name: None, value: None) ->  Options: ...
@overload
def option(name: str, value: None) -> str | bool | int | float: ...
@overload
def option(name: str, value: str | bool | int | float): ...
def option(name=None, value=None):
    """
    Sets or returns the value of a configuration option.

    If called without arguments, returns all configuration options as a
    dictionary. Returns an option's value if only called with the option's
    `name`. Otherwise sets the option to the given `value`.
    """
    if name is None:
        return options
    if name not in options:
        error = f'Configuration option "{name}" does not exist.'
        log.error(error)
        raise LookupError(error)
    if value is None:
        return options[name]
    else:
        options[name] = value


###########
# Storage #
###########

def location() -> Path:
    """
    Returns the default location of the configuration file.

    The folder returned by this function is platform-specific. It is inside the
    user's `AppData` folder on Windows, inside `.config` in the home directory
    on Linux, and in `Application Support` on macOS.
    """
    if system == 'Windows':
        return Path(os.environ['APPDATA'])/'MPh'
    elif system == 'Linux':
        return Path.home()/'.config'/'MPh'
    elif system == 'Darwin':
        return Path.home()/'Library'/'Application Support'/'MPh'
    else:
        return Path.home()/'MPh'


def load(file: Path | str = None):
    """
    Loads the configuration from the given `.ini` file.

    If `file` is not given, looks for a configuration file named `MPh.ini` in
    the current directory, or in the folder inside the user profile as returned
    by [`location()`](#location), or in this library's folder, in that order.
    If no such file is found, the hard-coded default values are used.
    """
    if not file:
        folders = [Path.cwd(), location(), Path(__file__).parent]
        for folder in folders:
            file = folder/'MPh.ini'
            if file.exists():
                break
        else:
            log.debug('Using default configuration.')
            return
    log.debug(f'Loading configuration from "{file}".')
    parser = ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(file, encoding='UTF-8')
    section = 'config'
    if section not in parser.sections():
        log.debug(f'Section [{section}] missing in configuration file.')
        return
    for (key, value) in options.items():
        if key in parser[section]:
            if isinstance(value, bool):
                options[key] = parser.getboolean(section, key)
            elif isinstance(value, int):
                options[key] = parser.getint(section, key)
            elif isinstance(value, float):
                options[key] = parser.getfloat(section, key)
            else:
                options[key] = parser[section][key]


def save(file: Path | str = None):
    """
    Saves the configuration in the given `.ini` file.

    If `file` is not given, saves the configuration in `MPh.ini` inside the
    default folder returned by [`location()`](#location).
    """
    if not file:
        file = location()/'MPh.ini'
    else:
        file = Path(file)
    parser = ConfigParser(interpolation=None)
    parser.optionxform = str
    section = 'config'
    parser.add_section(section)
    for (key, value) in options.items():
        parser[section][key] = str(value)
    file.parent.mkdir(exist_ok=True, parents=True)
    with file.open('w', encoding='UTF-8') as stream:
        parser.write(stream)


##########
# Init   #
##########

# Load custom configuration at start-up.
load()
