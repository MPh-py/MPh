"""Starts and stops the local Comsol session."""

from __future__ import annotations

from .client import Client
from .server import Server
from .config import option

import jpype

import atexit
import sys
import platform
import threading
import faulthandler
from logging import getLogger

from types import TracebackType


client = None
server = None
thread = None
system = platform.system()
log    = getLogger(__package__)


#########
# Start #
#########

def start(
    cores:   int = None,
    version: str = None,
    port:    int = 0,
) -> Client:
    """
    Starts a local Comsol session.

    This convenience function provides for the typical use case of running a
    Comsol session on the local machine, i.e. *not* have a client connect to a
    remote server elsewhere on the network.

    Example usage:
    ```python
    import mph
    client = mph.start(cores=1)
    model = client.load('model.mph')
    model.solve()
    model.save()
    client.remove(model)
    ```

    Returns a [`Client`](#Client) instance. Only one client can be instantiated
    at a time. Subsequent calls to `start()` will return the client instance
    created in the first call. In order to work around this limitation of the
    Comsol API, separate Python processes have to be started. Refer to section
    "[](/demonstrations.md#multiple-processes)" for guidance.

    By default, we communicate with the Comsol compute back-end in
    client–server mode. To run a stand-alone client, set `mph.option('session',
    'stand-alone')` up front. A stand-alone client starts up faster and reduces
    the call overhead to the Comsol API. However, it only works out of the box
    on Windows, but not Linux and macOS. Find more details in section
    "[](/limitations.md#platform-differences)".

    The number of `cores` (threads) the Comsol instance uses can be restricted
    by specifying a number. Otherwise all available cores will be used.

    A specific Comsol `version` can be selected if several are installed, for
    example `version='6.0'`. Otherwise the latest version is used.

    The server `port` can be specified if client–server mode is used. If
    omitted, the server chooses a random free port.
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

    # The default value for the session option used to be "platform-dependent",
    # which is why the option even exists. This distinction between operating
    # was removed in MPh 1.3. Otherwise we'd probably have no code for that
    # here in the `start()` function. So in a way this is legacy code that
    # might be deprecated at some point.
    session = option('session')
    if session == 'platform-dependent':
        if system == 'Windows':
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


########
# Stop #
########

exit_code = 0
exit_function = sys.exit
exception_handler = sys.excepthook


def exit_hook(code: int = None):
    """Monkey-patches `sys.exit()` to preserve exit code at shutdown."""
    global exit_code
    if isinstance(code, int):
        exit_code = code
    exit_function(code)


def exception_hook(
    exc_type:      type[BaseException],
    exc_value:     BaseException,
    exc_traceback: TracebackType | None,
):
    """Sets exit code to 1 if exception raised in main thread."""
    global exit_code
    exit_code = 1
    exception_handler(exc_type, exc_value, exc_traceback)


sys.exit = exit_hook
sys.excepthook = exception_hook


@atexit.register
def cleanup():
    """
    Cleans up resources at the end of the Python session.

    This function is not part of the public API. It runs automatically at the
    end of the Python session and is not intended to be called directly from
    application code.

    Stops the local server instance possibly created by `start()` and shuts
    down the Java Virtual Machine hosting the client instance.
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
        # `Client.__init__()`. pyTest seems to turn them back on right before
        # entering the exit sequence. On Linux, we do get the occasional
        # segmentation fault when running tests, just as pyTest exits. But
        # disabling the fault handler doesn't help, so let's not touch it. It
        # does seem to have some effect on Windows, but even there the benefit
        # is fairly unclear.
        if system == 'Windows' and faulthandler.is_enabled():
            log.debug('Turning off Python fault handlers.')
            faulthandler.disable()
        # Exit the hard way as Comsol leaves us no choice. See issue #38.
        jpype.java.lang.Runtime.getRuntime().exit(exit_code)
        # No Python code is reached from here on.
        # We would like to log that the Java VM has exited, but we can't.
