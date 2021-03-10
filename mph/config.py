"""Manages configuration options."""
__license__ = 'MIT'


########################################
# Options                              #
########################################

options = {
    'session': 'platform-dependent',
    'caching': False,
}
"""Default values for configuration options."""


def option(name=None, value=None):
    """
    Sets or returns the value of a configuration option.

    If called without arguments, returns all configuration options as
    a dictionary. Returns an option's value if only called with the
    option's `name`. Otherwise sets the option to the given `value`.
    """
    if name is None:
        return options
    elif value is None:
        return options[name]
    else:
        options[name] = value
