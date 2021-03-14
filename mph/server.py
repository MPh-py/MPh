"""Provides the wrapper for Comsol server instances."""
__license__ = 'MIT'


########################################
# Components                           #
########################################
from . import discovery                # back-end discovery


########################################
# Dependencies                         #
########################################
from subprocess import Popen as start  # background process
from subprocess import PIPE            # I/O redirection
from subprocess import TimeoutExpired  # communication time-out
from re import match as regex          # regular expression
from time import perf_counter as now   # wall-clock time
from time import sleep                 # execution delay
from sys import version_info           # Python version
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


########################################
# Server                               #
########################################
class Server:
    """
    Manages a Comsol server instance.

    Instances of this class start and eventually stop Comsol servers
    running on the local machine. Clients, either running on the same
    machine or elsewhere on the network, can then connect to the
    server at the port it exposes for that purpose.

    Example:
    ```python
        import mph
        server = mph.Server(cores=1)
        print(f'Server listing on port {server.port}.')
        server.stop()
    ```

    For this to work, make sure the Comsol server was started at least
    once from the command line, so that you have had a chance to define
    a user name and password.

    For client―server connections across the network, the server's
    host name or IP address has to be known up front by the client. It
    has to be either hard-coded or managed otherwise. Though if client
    and server run on the same machine, it is simply `"localhost"`.
    (However, *in* that situation, you may be better served — pardon
    the pun — to simply run a stand-alone client.)

    The first server starting on a given computer will typically accept
    client connections on TCP communication port 2036, as per Comsol's
    default configuration. Servers started subsequently will use port
    numbers of increasing value. The actual port number of a server
    instance can be accessed via its `port` attribute after it has
    started.

    The number of processor `cores` the server makes use of may be
    restricted. If no number is given, all cores are used by default.

    A specific `version` of the Comsol back-end can be specified if
    several are installed on the machine, for example `version='5.3a'`.
    Otherwise the latest version is used.

    A `timeout` can be set for the server to start up. The default
    is 60 seconds. Raises `TimeoutError` if the server failed to start
    within that period. Raises `RuntimeError` if user name and password
    for the server have not been set by the user.
    """

    def __init__(self, cores=None, version=None, timeout=60):

        # Start the Comsol server as an external process.
        backend = discovery.backend(version)
        server  = backend['server']
        logger.info('Starting external server process.')
        if cores:
            arguments = ['-np', str(cores)]
            noun = 'core' if cores == 1 else 'cores'
            logger.info(f'Server restricted to {cores} processor {noun}.')
        else:
            arguments = []
        arguments += ['-login', 'auto']
        command = server + arguments
        if version_info < (3, 8):
            command[0] = str(command[0])
        process = start(command, stdin=PIPE, stdout=PIPE, errors='ignore')

        # Wait for the server to report the port number.
        t0 = now()
        lines = []
        port = None
        while process.poll() is None:
            line = process.stdout.readline().strip()
            if line:
                lines.append(line)
            match = regex(r'(?i)^Comsol.+?server.+?(\d+)$', line.strip())
            if match:
                port = int(match.group(1))
                break
            if now() - t0 > timeout:
                error = 'Sever failed to start within time-out period.'
                logger.critical(error)
                raise TimeoutError(error)

        # Bail out if server exited with an error.
        # We don't use `process.returncode` here, as we would like to,
        # because on Linux the server executable exits with code 0,
        # indicating no error, even when an error has occurred.
        # We assume that the last line in the server's output is the
        # actual error message.
        if port is None:
            error = f'Starting server failed: {lines[-1]}'
            logger.critical(error)
            raise RuntimeError(error)
        logger.info(f'Server listening on port {port}.')

        # Save useful information in instance attributes.
        self.version = backend['name']
        self.cores   = cores
        self.port    = port
        self.process = process

    def running(self):
        """Returns whether the server process is still running."""
        return (self.process.poll() is None)

    def stop(self, timeout=10):
        """Shuts down the server."""
        if not self.running():
            logger.error(f'Server on port {self.port} has already stopped.')
            return
        logger.info(f'Telling the server on port {self.port} to shut down.')
        try:
            self.process.communicate(input='close', timeout=timeout)
            logger.info(f'Server on port {self.port} has stopped.')
        except TimeoutExpired:
            logger.info('Server did not shut down within time-out period.')
            logger.info('Forcefully terminating external server process.')
            self.process.kill()
            t0 = now()
            while self.running():
                if not self.running():
                    break
                if now() - t0 > timeout:
                    error = 'Forceful shutdown failed within time-out period.'
                    logger.critical(error)
                    raise TimeoutError(error) from None
                sleep(0.1)
            logger.info('Server process has been forcefully terminated.')
