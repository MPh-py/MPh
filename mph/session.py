"""Starts and stops the local Comsol session."""

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
import faulthandler                    # traceback dumps
from logging import getLogger          # event logging

########################################
# Globals                              #
########################################
client = None                          # client instance
server = None                          # server instance
thread = None                          # current thread
log    = getLogger(__package__)        # event log


########################################
# Start                                #
########################################

def start(cores=None, version=None, port=0):
    """
    Starts a local Comsol session.

    This convenience function provides for the typical use case of
    running a Comsol session on the local machine, i.e. *not* have a
    client connect to a remote server elsewhere on the network.

    Example usage:
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
    of the Comsol API. Subsequent calls to `start()` will return the
    client instance created in the first call. In order to work around
    this limitation, separate Python processes have to be started. Refer
    to section "Multiple processes" in documentation chapter
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
    global client, server, thread

    if not thread:
        thread = threading.current_thread()
    elif thread is not threading.current_thread():
        error = 'Cannot access client instance from different thread.'
        log.error(error)
        raise RuntimeError(error)

    if client:
        log.info('mph.start() returning the existing client instance.')
        return client

    session = option('session')
    if session == 'platform-dependent':
        if platform.system() == 'Windows':
            session = 'stand-alone'
        else:
            session = 'client-server'

    log.info('Starting local Comsol session.')
    if session == 'stand-alone':
        client = Client(cores=cores, version=version)
    elif session == 'client-server':
        server = Server(cores=cores, version=version, port=port)
        client = Client(cores=cores, version=version, port=server.port)
    else:
        error = f'Invalid session type "{session}".'
        log.error(error)
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


exit_code = 0
exit_function = sys.exit
sys.exit = exit_hook

exception_handler_sys = sys.excepthook
sys.excepthook = exception_hook_sys


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
            log.exception(error)
    if jpype.isJVMStarted():
        log.info('Exiting the Java virtual machine.')
        # Work around Unix-style "lazy writing" before we pull the plug.
        sys.stdout.flush()
        sys.stderr.flush()
        # Only deactivate fault handler on Windows, just like we do in
        # `Client.__init__()`. pyTest seems to turn them back on right
        # before entering the exit sequence. On Linux, we do get the
        # occasional segmentation fault when running tests, just as
        # pyTest exits. But disabling the fault handler doesn't help,
        # so let's not touch it. It does seem to have some effect on
        # Windows, but even there the benefit is fairly unclear.
        if platform.system() == 'Windows' and faulthandler.is_enabled():
            log.debug('Turning off Python fault handlers.')
            faulthandler.disable()
        # Exit the hard way as Comsol leaves us no choice. See issue #38.
        jpype.java.lang.Runtime.getRuntime().exit(exit_code)
        # No Python code is reached from here on.
        # We would like to log that the Java VM has exited, but we can't.
        # log.info('Java virtual machine has exited.')
