"""Pythonic scripting interface for Comsol Multiphysics"""

# Meta information
__title__     = 'MPh'
__version__   = '1.0.0'
__date__      = '2021–04–13'
__author__    = 'John Hennig'
__copyright__ = 'John Hennig'
__license__   = 'MIT'

# Public interface
from .session import start
from .config  import option
from .client  import Client
from .server  import Server
from .model   import Model
from .node    import Node
from .node    import inspect
from .node    import tree
