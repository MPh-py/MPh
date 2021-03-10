"""Pythonic scripting interface for Comsol Multiphysics"""

# Meta information
__title__     = 'MPh'
__version__   = '0.9.0'
__date__      = '2021–03–10'
__author__    = 'John Hennig'
__copyright__ = 'John Hennig'
__license__   = 'MIT'

# Public interface
from .session import start
from .model   import Model
from .client  import Client
from .server  import Server
from .config  import option
from .tools   import inspect
