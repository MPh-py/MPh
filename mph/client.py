"""Provides the wrapper for a Comsol client instance."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from . import backend                  # back-end information
from .model import Model               # model object


########################################
# Dependencies                         #
########################################
import jpype                           # Java bridge
import jpype.imports                   # Java object imports
import atexit                          # exit handler
import os                              # operating system
from pathlib import Path               # file paths
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # package-wide event logger


########################################
# Client                               #
########################################
class Client:
    """
    Represents the (single) Comsol client instance.

    A client can either be a stand-alone instance or it could connect
    to a Comsol server started independently, possibly on a different
    machine on the network.

    Example:
    ```python
        import mph
        client = mph.Client(cores=1)
        model = client.load('model.mph')
        client.remove(model)
    ```

    Due to limitations of the Java bridge, provided by the JPype
    library, only one client can be instantiated at a time. This is
    because JPype cannot manage more than one Java virtual machine
    within the same Python session. Separate Python processes would
    have to be run to work around this limitation.

    The number of `cores` (threads) the client instance uses can
    be restricted by specifying a number. Otherwise all available
    cores are used.

    A specific Comsol `version` can be selected if several are
    installed, for example `version='5.3a'`. Otherwise the latest
    version is used.

    Initializes a stand-alone Comsol session if no `port` number is
    specified. Otherwise tries to connect to the Comsol server listening
    at the given port for client connections. The `host` address defaults
    to `'localhost'`, but could be any domain name or IP address.

    Raises `RuntimeError` if another client is already running.

    Internally, the client is a wrapper around the `ModelUtil` object
    provided by Comsol's Java API, which can be accessed directly via
    the `.java` instance attribute.
    """

    def __init__(self, cores=None, version=None, port=None, host='localhost'):

        # Make sure this is the first (and only) client created.
        if jpype.isJVMStarted():
            error = 'Only one client can be instantiated at a time.'
            logger.error(error)
            raise RuntimeError(error)

        # Determine relevant folders of the Comsol back-end.
        main = backend.folder(version)
        arch = backend.architecture()
        jre  = main / 'java' / arch / 'jre' / 'bin'
        jvm  = jre / 'server' / 'jvm.dll'
        api  = main / 'plugins' / '*'

        # Manipulate binary search path to only point to Comsol's JVM.
        path = os.environ['PATH']
        os.environ['PATH'] = str(jre)

        # Set environment variable so Comsol will restrict cores at start-up.
        if cores:
            os.environ['COMSOL_NUM_THREADS'] = str(cores)

        # Start the Java virtual machine.
        logger.info(f'JPype version is {jpype.__version__}.')
        logger.info('Starting Java virtual machine.')
        jpype.startJVM(str(jvm), classpath=str(api), convertStrings=False)
        from com.comsol.model.util import ModelUtil as java
        logger.info('Java virtual machine has started.')

        # Restore the original search path.
        os.environ['PATH'] = path

        # Connect to a server if requested.
        if port is not None:
            logger.info(f'Connecting to server "{host}" at port {port}.')
            java.connect(host, port)
        # Otherwise initialize stand-alone session.
        else:
            logger.info('Initializing stand-alone client.')
            graphics = False
            java.initStandalone(graphics)
            logger.info('Stand-alone client initialized.')

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

        # Save setup in instance attributes.
        self.cores   = cores
        self.version = list(backend.versions().keys())[-1]
        self.host    = host
        self.port    = port
        self.folder  = main
        self.java    = java

    def load(self, file):
        """Returns the model loaded from the given `file`."""
        file = Path(file)
        tag = self.java.uniquetag('model')
        logger.info(f'Loading model "{file.name}".')
        model = Model(self.java.load(tag, str(file)))
        logger.info('Finished loading model.')
        return model

    def create(self, name):
        """
        Creates and returns a new, empty model with the given `name`.

        This is not particularly useful unless you are prepared to
        drop down to the Java layer and add model features on your
        own. It may help to call the returned (Python) model object
        something like `pymodel` and assign the name `model` to
        `pymodel.java`. Then you can just copy-and-paste Java or
        Matlab code from the Comsol programming manual or as exported
        from the Comsol front-end. Python will gracefully overlook
        gratuitous semicolons at the end of statements, so this
        approach would even work for entire blocks of code.
        """
        java = self.java.createUnique('model')
        logger.debug(f'Created model with tag "{java.tag()}".')
        model = Model(java)
        model.rename(name)
        return model

    def models(self):
        """Returns all model objects currently held in memory."""
        return [Model(self.java.model(tag)) for tag in self.java.tags()]

    def names(self):
        """Names all models that are currently held in memory."""
        return [model.name() for model in self.models()]

    def remove(self, model):
        """Removes the given `model` from memory."""
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
        if self.port is not None:
            self.java.disconnect()
            self.host = None
            self.port = None
        else:
            error = 'A stand-alone client cannot disconnect from a server.'
            logger.error(error)
            raise RuntimeError(error)


@atexit.register
def shutdown():
    """
    Shuts down the Java virtual machine when the Python session ends.

    This function is not part of the public API. It runs automatically
    at the end of the Python session and should not be called directly
    from application code.
    """
    if jpype.isJVMStarted():
        if jpype.__version__ > '0.7.5':
            logger.info('Exiting the Java virtual machine.')
            jpype.java.lang.Runtime.getRuntime().exit(0)
        else:
            logger.info('Shutting down the Java virtual machine.')
            jpype.shutdownJVM()
        logger.info('Java virtual machine has shut down.')
