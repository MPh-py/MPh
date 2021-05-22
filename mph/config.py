"""Manages configuration options."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger

options = {
    'session':  'platform-dependent',
    'caching':  False,
    'classkit': False,
}
"""Default values for configuration options."""


########################################
# Option                               #
########################################

def option(name=None, value=None):
    """
    Sets or returns the value of a configuration option.

    If called without arguments, returns all configuration options as
    a dictionary. Returns an option's value if only called with the
    option's `name`. Otherwise sets the option to the given `value`.
    """
    if name is None:
        return options
    if name not in options:
        error = f'Configuration option "{name}" does not exist.'
        logger.error(error)
        raise LookupError(error)
    if value is None:
        return options[name]
    else:
        options[name] = value
