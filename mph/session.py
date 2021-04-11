"""Starts and stops the local Comsol session."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from .client import Client             # client class
from .server import Server             # server class
from .config import option             # configuration


########################################
# Dependencies                         #
########################################
import jpype                           # Java bridge
import atexit                          # exit handler
import sys                             # system specifics
import platform                        # platform information
import threading                       # multi-threading
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
client = None                          # client instance
server = None                          # server instance
logger = getLogger(__package__)        # event logger


########################################
# Start                                #
########################################

def start(cores=None, version=None, port=0):
    """
    Starts a local Comsol session.

    This convenience function provides for the typical use case of
    running a Comsol session on the local machine, i.e. *not* have a
    client connect to a remote server elsewhere on the network.

    Example:
    ```python
        import mph
        client = mph.start(cores=1)
        model = client.load('model.mph')
        model.solve()
        model.save()
        client.remove(model)
    ```

    Depending on the platform, this may either be a stand-alone client
    (on Windows) or a thin client connected to a server running locally
    (on Linux and macOS). The reason for this disparity is that, while
    stand-alone clients are more lightweight and start up much faster,
    support for this mode of operation is limited on Unix-like operating
    systems, and thus not the default. Find more details in documentation
    chapter "Limitations".

    Only one client can be instantiated at a time. This is a limitation
    of the Python-to-Java bridge JPype, which cannot manage more than
    one Java virtual machine within the same Python process. Therefore
    `start()` can only be called once. Subsequent calls will raise
    `NotImplementedError`. Separate Python processes have to be started
    to work around this issue. Refer to documentation chapter
    "Demonstrations" for guidance.

    The number of `cores` (threads) the Comsol instance uses can be
    restricted by specifying a number. Otherwise all available cores
    will be used.

    A specific Comsol `version` can be selected if several are
    installed, for example `version='5.3a'`. Otherwise the latest
    version is used.

    The server `port` can be specified if client–server mode is used.
    If omitted, the server chooses a random free port.
    """
    global client, server

    if client or server:
        error = 'Only one Comsol session can be started in the same process.'
        logger.error(error)
        raise NotImplementedError(error)

    session = option('session')
    if session == 'platform-dependent':
        if platform.system() == 'Windows':
            session = 'stand-alone'
        else:
            session = 'client-server'

    logger.info('Starting local Comsol session.')
    if session == 'stand-alone':
        client = Client(cores=cores, version=version)
    elif session == 'client-server':
        server = Server(cores=cores, version=version, port=port)
        client = Client(cores=cores, version=version, port=server.port)
    else:
        error = f'Invalid session type "{session}".'
        logger.error(error)
        raise ValueError(error)
    return client


########################################
# Stop                                 #
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
def cleanup():
    """
    Cleans up resources at the end of the Python session.

    This function is not part of the public API. It runs automatically
    at the end of the Python session and is not intended to be called
    directly from application code.

    Stops the local server instance possibly created by `start()` and
    shuts down the Java Virtual Machine hosting the client instance.
    """
    if client and client.port:
        try:
            client.disconnect()
        except Exception:
            error = 'Error while disconnecting client at session clean-up.'
            logger.exception(error)
    if server and server.running():
        server.stop()
    if jpype.isJVMStarted():
        logger.info('Exiting the Java virtual machine.')
        sys.stdout.flush()
        sys.stderr.flush()
        jpype.java.lang.Runtime.getRuntime().exit(exit_code)
        # No code is reached from here on due to the hard exit of the JVM.
        logger.info('Java virtual machine has exited.')
