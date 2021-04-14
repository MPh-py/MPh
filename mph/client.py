"""Provides the wrapper for a Comsol client instance."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from . import discovery                # back-end discovery
from .model import Model               # model class
from .config import option             # configuration


########################################
# Dependencies                         #
########################################
import jpype                           # Java bridge
import jpype.imports                   # Java object imports
import platform                        # platform information
import os                              # operating system
from pathlib import Path               # file-system paths
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


########################################
# Client                               #
########################################
class Client:
    """
    Manages the Comsol client instance.

    A client can either be a stand-alone instance or it could connect
    to a Comsol server instance started independently, possibly on a
    different machine on the network.

    Example:
    ```python
        import mph
        client = mph.Client(cores=1)
        model = client.load('model.mph')
        model.solve()
        model.save()
        client.remove(model)
    ```

    Due to limitations of the Java bridge, provided by the JPype
    library, only one client can be instantiated at a time. This is
    because JPype cannot manage more than one Java virtual machine
    within the same Python session. Separate Python processes would
    have to be started, or spawned, to work around this limitation.
    `NotImplementedError` is therefore raised if another client is
    already running.

    The number of `cores` (threads) the client instance uses can
    be restricted by specifying a number. Otherwise all available
    cores are used.

    A specific Comsol `version` can be selected if several are
    installed, for example `version='5.3a'`. Otherwise the latest
    version is used, and reported via the `.version` attribute.

    Initializes a stand-alone Comsol session if no `port` number is
    specified. Otherwise tries to connect to the Comsol server
    listening at the given port for client connections. The `host`
    address defaults to `'localhost'`, but could be any domain name
    or IP address.

    Internally, the client is a wrapper around the `ModelUtil` object
    provided by Comsol's Java API, which may also be accessed directly
    via the instance attribute `.java`.
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, cores=None, version=None, port=None, host='localhost'):

        # Make sure this is the one and only client.
        if jpype.isJVMStarted():
            error = 'Only one client can be instantiated at a time.'
            logger.error(error)
            raise NotImplementedError(error)

        # Discover Comsol back-end.
        backend = discovery.backend(version)

        # Instruct Comsol to limit number of processor cores to use.
        if cores:
            os.environ['COMSOL_NUM_THREADS'] = str(cores)

        # Start the Java virtual machine.
        logger.debug(f'JPype version is {jpype.__version__}.')
        logger.info('Starting Java virtual machine.')
        jpype.startJVM(str(backend['jvm']),
                       classpath=str(backend['root']/'plugins'/'*'),
                       convertStrings=False)
        logger.info('Java virtual machine has started.')

        # Initialize a stand-alone client if no server port given.
        from com.comsol.model.util import ModelUtil as java
        if port is None:
            logger.info('Initializing stand-alone client.')
            check_environment(backend)
            graphics = True
            java.initStandalone(graphics)
            logger.info('Stand-alone client initialized.')
        # Otherwise skip stand-alone initialization and connect to server.
        else:
            logger.info(f'Connecting to server "{host}" at port {port}.')
            java.connect(host, port)

        # Log number of used processor cores as reported by Comsol instance.
        cores = java.getPreference('cluster.processor.numberofprocessors')
        cores = int(str(cores))
        noun = 'core' if cores == 1 else 'cores'
        logger.info(f'Running on {cores} processor {noun}.')

        # Load Comsol settings from disk so as to not just use defaults.
        java.loadPreferences()

        # Override certain settings not useful in headless operation.
        java.setPreference('updates.update.check', 'off')
        java.setPreference('tempfiles.saving.warnifoverwriteolder', 'off')
        java.setPreference('tempfiles.recovery.autosave', 'off')
        java.setPreference('tempfiles.recovery.checkforrecoveries', 'off')
        java.setPreference('tempfiles.saving.optimize', 'filesize')

        # Save useful information in instance attributes.
        self.version = backend['name']
        self.cores   = cores
        self.host    = host
        self.port    = port
        self.java    = java

    def __repr__(self):
        connection = f'port={self.port}' if self.port else 'stand-alone'
        return f"{self.__class__.__name__}({connection})"

    def __contains__(self, item):
        if isinstance(item, str):
            if item in self.names():
                return True
        elif isinstance(item, Model):
            if item in self.models():
                return True
        return False

    def __iter__(self):
        yield from self.models()

    def __truediv__(self, name):
        if isinstance(name, str):
            for model in self:
                if name == model.name():
                    return model
            else:
                error = f'Model "{name}" has not been loaded by client.'
                logger.error(error)
                raise ValueError(error)
        return NotImplemented

    ####################################
    # Inspection                       #
    ####################################

    def models(self):
        """Returns all models currently held in memory."""
        return [Model(self.java.model(tag)) for tag in self.java.tags()]

    def names(self):
        """Returns the names of all loaded models."""
        return [model.name() for model in self.models()]

    def files(self):
        """Returns the file-system paths of all loaded models."""
        return [model.file() for model in self.models()]

    ####################################
    # Interaction                      #
    ####################################

    def load(self, file):
        """Loads a model from the given `file` and returns it."""
        file = Path(file).resolve()
        if self.caching() and file in self.files():
            logger.info(f'Retrieving "{file.name}" from cache.')
            return self.models()[self.files().index(file)]
        tag = self.java.uniquetag('model')
        logger.info(f'Loading model "{file.name}".')
        model = Model(self.java.load(tag, str(file)))
        logger.info('Finished loading model.')
        return model

    def caching(self, state=None):
        """
        Enables or disables caching of previously loaded models.

        Caching means that the `load()` method will check if a model
        has been previously loaded from the same file-system path and,
        if so, return the in-memory model object instead of reloading
        it from disk. By default (at start-up) caching is disabled.

        Pass `True` to enable caching, `False` to disable it. If no
        argument is passed, the current state is returned.
        """
        if state is None:
            return option('caching')
        elif state in (True, False):
            option('caching', state)
        else:
            error = 'Caching state can only be set to either True or False.'
            logger.error(error)
            raise ValueError(error)

    def create(self, name=None):
        """
        Creates a new model and returns it as a `Model` instance.

        An optional `name` can be supplied. Otherwise the model will
        retain its automatically generated name, like "Model 1".
        """
        java = self.java.createUnique('model')
        model = Model(java)
        if name:
            model.rename(name)
        else:
            name = model.name()
        logger.debug(f'Created model "{name}" with tag "{java.tag()}".')
        return model

    def remove(self, model):
        """Removes the given `model` from memory."""
        if isinstance(model, str):
            if model not in self.names():
                error = f'No model named "{model}" exists.'
                logger.error(error)
                raise ValueError(error)
            model = self[model]
        elif isinstance(model, Model):
            if model not in self.models():
                error = f'Model "{model}" does not exist.'
                logger.error(error)
                raise ValueError(error)
        else:
            error = 'Model must either be a model name or Model instance.'
            logger.error(error)
            raise TypeError(error)
        name = model.name()
        tag  = model.java.tag()
        logger.debug(f'Removing model "{name}" with tag "{tag}".')
        self.java.remove(tag)

    def clear(self):
        """Removes all loaded models from memory."""
        logger.debug('Clearing all models from memory.')
        self.java.clear()

    def disconnect(self):
        """Disconnects the client from the server."""
        if self.port:
            self.java.disconnect()
            self.host = None
            self.port = None
        else:
            error = 'The client is not connected to a server.'
            logger.error(error)
            raise RuntimeError(error)


########################################
# Environment                          #
########################################

def check_environment(backend):
    """Checks the process environment required for a stand-alone client."""
    system = platform.system()
    root = backend['root']
    help = 'Refer to chapter "Limitations" in the documentation for help.'
    if system == 'Windows':
        pass
    elif system == 'Linux':
        var = 'LD_LIBRARY_PATH'
        if var not in os.environ:
            error = f'Library search path {var} not set in environment.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        path = os.environ[var].split(os.pathsep)
        lib = root/'lib'/'glnxa64'
        if str(lib) not in path:
            error = f'Folder "{lib}" missing in library search path.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        gcc = root/'lib'/'glnxa64'/'gcc'
        if gcc.exists() and str(gcc) not in path:
            logger.warning(f'Folder "{gcc}" missing in library search path.')
        gra = str(root/'ext'/'graphicsmagick'/'glnxa64')
        if str(gra) not in path:
            error = f'Folder "{gra}" missing in library search path.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        cad = root/'ext'/'cadimport'/'glnxa64'
        if cad.exists() and str(cad) not in path:
            logger.warning(f'Folder "{cad}" missing in library search path.')
    elif system == 'Darwin':
        var = 'DYLD_LIBRARY_PATH'
        if var not in os.environ:
            error = f'Library search path {var} not set in environment.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        if var in os.environ:
            path = os.environ[var].split(os.pathsep)
        else:
            path = []
        lib = root/'lib'/'maci64'
        if str(lib) not in path:
            error = f'Folder "{lib}" missing in library search path.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        gra = root/'ext'/'graphicsmagick'/'maci64'
        if str(gra) not in path:
            error = f'Folder "{gra}" missing in library search path.'
            logger.error(error)
            raise RuntimeError(error + '\n' + help)
        cad = root/'ext'/'cadimport'/'maci64'
        if cad.exists() and str(cad) not in path:
            logger.warning(f'Folder "{cad}" missing in library search path.')
