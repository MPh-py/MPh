﻿"""Provides the wrapper for Comsol server instances."""

from __future__ import annotations

from .       import discovery
from .config import option

from subprocess import Popen as start
from subprocess import PIPE
from subprocess import TimeoutExpired
from re         import match as regex
from time       import perf_counter as now
from logging    import getLogger

from typing import Literal


log = getLogger(__package__)


##########
# Server #
##########

class Server:
    """
    Manages a Comsol server process.

    Instances of this class start and eventually stop Comsol servers
    running on the local machine. Clients, either running on the same
    machine or elsewhere on the network, can then connect to the
    server at the network port it exposes for that purpose.

    Example usage:
    ```python
    import mph
    server = mph.Server(cores=1)
    print(f'Server listing on port {server.port}.')
    server.stop()
    ```

    The number of processor `cores` the server makes use of may be
    restricted. If no number is given, all cores are used by default.

    A specific `version` of the Comsol back-end can be specified if
    several are installed on the machine, for example `version='6.0'`.
    Otherwise the latest version is used.

    The server can be instructed to use a specific network `port` for
    communication with clients by passing the number of a free port
    explicitly. If `port=None`, the default, the server will try to
    use port 2036 or, in case it is blocked by another server already
    running, will try subsequent numbers until it finds a free port.
    This is also Comsol's default behavior. It is however not robust
    and may lead to start-up failures if multiple servers are spinning
    up at the same time. Pass `port=0` to work around this issue. The
    server will then select a random free port, which will almost always
    avoid collisions.

    If `multi` is `False` or `'off'` or `None` (the default), then
    the server will shut down as soon as the first connected clients
    disconnects itself. If it is `True` or `'on'`, the server process
    will stay alive and accept multiple client connections.

    A `timeout` can be set for the server start-up. The default is 60
    seconds. `TimeoutError` is raised if the server failed to start
    within that period.

    A list of extra command-line `arguments` can be specified. They are
    appended to the arguments passed by default when starting the
    server process, and would thus override them in case of duplicates.
    """

    def __init__(self,
        cores:     int = None,
        version:   str = None,
        port:      int = None,
        multi:     bool | Literal['on', 'off'] | None = None,
        timeout:   int = 60,
        arguments: list[str] = None,
    ):

        # Remember user-provided command-line arguments.
        extra_arguments = arguments if arguments else []

        # Start Comsol server as an external process.
        backend = discovery.backend(version)
        server  = backend['server']
        log.info('Starting external server process.')
        arguments = ['-login', 'auto', '-graphics', '-autosave', 'off']
        if option('classkit'):
            arguments += ['-ckl']
        if cores:
            arguments += ['-np', str(cores)]
            noun = 'core' if cores == 1 else 'cores'
            log.info(f'Server restricted to {cores} processor {noun}.')
        if port is not None:
            arguments += ['-port', str(port)]
        if multi:
            if multi in (True, 'on'):
                arguments += ['-multi', 'on']
            elif multi in (False, 'off'):
                arguments += ['-multi', 'off']
            else:
                error = f'Invalid value "{multi}" for option "multi".'
                log.error(error)
                raise ValueError(error)
        command = server + arguments + extra_arguments
        command[0] = str(command[0])   # Required for Python 3.6 and 3.7.
        process = start(command, stdin=PIPE, stdout=PIPE, errors='ignore')

        # Remember the requested port (if any).
        requested = port

        # Wait for the server to report the port number.
        t0 = now()
        lines = []
        port = None
        while process.poll() is None:
            line = process.stdout.readline().strip()
            if line:
                lines.append(line)
            port = parse_port(line)
            if port:
                break
            if now() - t0 > timeout:
                error = 'Sever failed to start within time-out period.'
                log.error(error)
                raise TimeoutError(error)

        # Bail out if server exited with an error.
        # We don't use `process.returncode` here, as we would like to,
        # because on Linux the server executable exits with code 0,
        # indicating no error, even when an error has occurred.
        # We assume that the last line in the server's output is the
        # actual error message.
        if port is None:
            error = f'Starting server failed: {lines[-1]}'
            log.error(error)
            raise RuntimeError(error)
        log.info(f'Server listening on port {port}.')

        # Verify port number is correct if a specific one was requested.
        if requested and port != requested:
            error = f'Server port is {port}, but {requested} was requested.'
            log.error(error)
            raise RuntimeError(error)

        # Save information in instance attributes.
        self.version = backend['name']
        """Comsol version (e.g., `'6.0'`) the server is running on."""
        self.cores = cores
        """Number of processor cores the server was requested to use."""
        self.port = port
        """Port number the server is listening on for client connections."""
        self.process = process
        """Subprocess that the server is running in."""

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(port={self.port})'

    def running(self) -> bool:
        """Returns whether the server process is still running."""
        return (self.process.poll() is None)

    def stop(self, timeout: int = 20):
        """Shuts down the server."""
        if not self.running():
            log.error(f'Server on port {self.port} has already stopped.')
            return
        log.info(f'Telling the server on port {self.port} to shut down.')
        try:
            self.process.communicate(input='close', timeout=timeout)
            log.info(f'Server on port {self.port} has stopped.')
        except TimeoutExpired:
            log.warning('Server did not shut down within time-out period.')
            log.info('Trying to forcefully terminate server process.')
            self.process.kill()


###########
# Parsing #
###########

def parse_port(line: str) -> int | None:
    """Parses out the port number from a line of server output."""
    match = regex(r'^COMSOL.* \(.*\) .*?(\d{4,5}).*$', line)
    if match:
        port = int(match.group(1))
        return port
    else:
        return None
