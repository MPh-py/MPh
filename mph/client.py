"""Provides the wrapper for a Comsol client instance."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from . import discovery                # back-end discovery
from .model import Model               # model class


########################################
# Dependencies                         #
########################################
import jpype                           # Java bridge
import jpype.imports                   # Java object imports
import platform                        # platform information
import atexit                          # exit handler
import os                              # operating system
import sys                             # system specifics
import threading                       # multi-threading
from pathlib import Path               # file-system paths
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

    def __init__(self, cores=None, version=None, port=None, host='localhost'):

        # Make sure this is the one and only client.
        if jpype.isJVMStarted():
            error = 'Only one client can be instantiated at a time.'
            logger.error(error)
            raise NotImplementedError(error)

        # Discover Comsol back-end.
        backend = discovery.backend(version)

        # Set environment variables for loading external libraries.
        system = platform.system()
        root = backend['root']
        if system == 'Windows':
            var = 'PATH'
            if var in os.environ:
                path = os.environ[var].split(os.pathsep)
            else:
                path = []
            lib = str(root/'lib'/'glnxa64')
            if lib not in path:
                os.environ[var] = os.pathsep.join([lib] + path)
        elif system == 'Linux':
            lib = str(root/'lib'/'glnxa64')
            gcc = str(root/'lib'/'glnxa64'/'gcc')
            ext = str(root/'ext'/'graphicsmagick'/'glnxa64')
            cad = str(root/'ext'/'cadimport'/'glnxa64')
            pre = str(root/'java'/'glnxa64'/'jre'/'lib'/'amd64'/'libjsig.so')
            var = 'LD_LIBRARY_PATH'
            if var in os.environ:
                path = os.environ[var].split(os.pathsep)
            else:
                path = []
            if lib not in path:
                os.environ[var] = os.pathsep.join([lib, gcc, ext, cad] + path)
            vars = ('MAGICK_CONFIGURE_PATH', 'MAGICK_CODER_MODULE_PATH',
                    'MAGICK_FILTER_MODULE_PATH')
            for var in vars:
                os.environ[var] = ext
            os.environ['LD_PRELOAD'] = pre
            os.environ['LC_NUMERIC'] = os.environ['LC_ALL'] = 'C'
        elif system == 'Darwin':
            var = 'DYLD_LIBRARY_PATH'
            if var in os.environ:
                path = os.environ[var].split(os.pathsep)
            else:
                path = []
            lib = str(root/'lib'/'maci64')
            ext = str(root/'ext'/'graphicsmagick'/'maci64')
            cad = str(root/'ext'/'cadimport'/'maci64')
            if lib not in path:
                os.environ[var] = os.pathsep.join([lib, ext, cad] + path)

        # Instruct Comsol to limit number of processor cores to use.
        if cores:
            os.environ['COMSOL_NUM_THREADS'] = str(cores)

        # Start the Java virtual machine.
        logger.info(f'JPype version is {jpype.__version__}.')
        logger.info('Starting Java virtual machine.')
        jpype.startJVM(str(backend['jvm']),
                       classpath=str(root/'plugins'/'*'),
                       convertStrings=False)
        logger.info('Java virtual machine has started.')

        # Initialize a stand-alone client if no server port given.
        from com.comsol.model.util import ModelUtil as java
        if port is None:
            logger.info('Initializing stand-alone client.')
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
        try:
            java.setPreference('tempfiles.recovery.checkforrecoveries', 'off')
        except Exception:
            logger.warning('Could not turn off check for recovery files.')
        java.setPreference('tempfiles.saving.optimize', 'filesize')

        # Save useful information in instance attributes.
        self.version = backend['name']
        self.cores   = cores
        self.host    = host
        self.port    = port
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


########################################
# Shutdown                             #
########################################


def exit_hook(code=None):
    """Monkey-patches `sys.exit()` to preserve exit code at shutdown."""
    global exit_code
    if isinstance(code, int):
        exit_code = code
    exit_function(code)


def exception_hook_sys(exc_type, exc_value, exc_traceback):
    """Sets exit code to 1 if exception raised in main thread."""
    global exit_code
    exit_code = 1
    exception_handler_sys(exc_type, exc_value, exc_traceback)


def exception_hook_threads(info):
    """Sets exit code to 1 if exception raised in any other thread."""
    global exit_code
    exit_code = 1
    exception_handler_threads(info)


exit_code = 0
exit_function = sys.exit
sys.exit = exit_hook

exception_handler_sys = sys.excepthook
sys.excepthook = exception_hook_sys

# Only available as of Python 3.8, see bugs.python.org/issue1230540.
if hasattr(threading, 'excepthook'):
    exception_handler_threads = threading.excepthook
    threading.excepthook = exception_hook_threads


@atexit.register
def shutdown():
    """
    Shuts down the Java virtual machine when the Python session ends.

    This function is not part of the public API. It runs automatically
    at the end of the Python session and should not be called directly
    from application code.
    """
    if jpype.isJVMStarted():
        logger.info('Exiting the Java virtual machine.')
        sys.stdout.flush()
        sys.stderr.flush()
        jpype.java.lang.Runtime.getRuntime().exit(exit_code)
        # No code is reached after this due to the hard exit of the JVM.
        logger.info('Java virtual machine has exited.')
