"""Provides the wrapper for a Comsol client instance."""

from __future__ import annotations

from .       import discovery
from .model  import Model
from .config import option

import jpype
import jpype.imports                      # noqa: F401 (imported, but not used)

import os
import faulthandler
from pathlib import Path
from logging import getLogger

from typing          import overload
from collections.abc import Iterator
from jpype           import JClass


# The following look-up table is used by the `modules()` method. It is based on
# the table on page 42 of Comsol 6.3's Programming Reference Manual, with the
# two columns swapped. It thus maps vendor strings to product names (add-on
# modules), except that we also shorten the names somewhat (drop "Module"
# everywhere) and leave out the pointless trademark symbols. The vendor strings
# are what we need to query the `ModelUtil.hasProduct()` Java method.
modules = {
    'COMSOL':                   'Comsol core',
    'ACDC':                     'AC/DC',
    'ACOUSTICS':                'Acoustics',
    'BATTERYDESIGN':            'Battery Design',
    'CADIMPORT':                'CAD Import',
    'CFD':                      'CFD',
    'CHEM':                     'Chemical Reaction Engineering',
    'CLUSTERNODE':              'Cluster Computing',
    'COMPOSITEMATERIALS':       'Composite Materials',
    'CORROSION':                'Corrosion',
    'DESIGN':                   'Design',
    'ECADIMPORT':               'ECAD Import',
    'ELECTRICDISCHARGE':        'Electric Discharge',
    'ELECTROCHEMISTRY':         'Electrochemistry',
    'ELECTRODEPOSITION':        'Electrodeposition',
    'FATIGUE':                  'Fatigue',
    'CATIA5':                   'File Import for Catia v5',
    'FUELCELLANDELECTROLYZER':  'Fuel Cell & Electrolyzer',
    'GEOMECHANICS':             'Geomechanics',
    'HEATTRANSFER':             'Heat Transfer',
    'LIQUIDANDGASPROPERTIES':   'Liquid & Gas Properties',
    'LLAUTOCAD':                'LiveLink AutoCAD',
    'LLCREOPARAMETRIC':         'LiveLink PTC Creo Parametric',
    'LLEXCEL':                  'LiveLink Excel',
    'LLINVENTOR':               'LiveLink Inventor',
    'LLMATLAB':                 'LiveLink Matlab',
    'LLREVIT':                  'LiveLink Revit',
    'LLPROENGINEER':            'LiveLink PTC Pro/ENGINEER',
    'LLSOLIDEDGE':              'LiveLink Solid Edge',
    'LLSOLIDWORKS':             'LiveLink SolidWorks',
    'MEMS':                     'MEMS',
    'MICROFLUIDICS':            'Microfluidics',
    'MIXER':                    'Mixer',
    'MOLECULARFLOW':            'Molecular Flow',
    'MULTIBODYDYNAMICS':        'Multibody Dynamics',
    'NONLINEARSTRUCTMATERIALS': 'Nonlinear Structural Materials',
    'OPTIMIZATION':             'Optimization',
    'PARTICLETRACING':          'Particle Tracing',
    'PIPEFLOW':                 'Pipe Flow',
    'PLASMA':                   'Plasma',
    'POLYMERFLOW':              'Polymer Flow',
    'RAYOPTICS':                'Ray Optics',
    'RF':                       'RF',
    'ROTORDYNAMICS':            'Rotordynamics',
    'SEMICONDUCTOR':            'Semiconductor',
    'STRUCTURALMECHANICS':      'Structural Mechanics',
    'SUBSURFACEFLOW':           'Subsurface Flow',
    'UQ':                       'Uncertainty Quantification',
    'WAVEOPTICS':               'Wave Optics',
}


log = getLogger(__package__)


class Client:
    """
    Manages the Comsol client instance.

    A client can connect to a Comsol server started independently, possibly on
    a different machine on the network, unless it is a stand-alone client
    running independently.

    Example usage:
    ```python
    import mph
    client = mph.Client(cores=1)
    model = client.load('model.mph')
    model.solve()
    model.save()
    client.remove(model)
    ```

    The number of `cores` (threads) the client instance uses can be restricted
    by specifying a number. Otherwise all available cores are used.

    A specific Comsol `version` can be selected if several are installed, for
    example `version='6.0'`. Otherwise the latest version is used.

    Initializes a stand-alone Comsol session if no `port` number is specified.
    Otherwise tries to connect to the Comsol server listening at the given port
    for client connections.

    The `host` address defaults to `'localhost'`, but could be any domain name
    or IP address. If `host=None` is passed, the client will remain in a
    disconnected state until [`connect()`](#connect) is called. This is
    sometimes useful to catch run-time errors at start-up.

    This class is a wrapper around the [`com.comsol.model.util.ModelUtil`][1]
    Java class, which itself is wrapped by JPype and can be accessed directly
    via the `.java` attribute. The full Comsol functionality is thus available
    if needed.

    However, as that Comsol class is a singleton, i.e. a static class that
    cannot be instantiated, we can only run one client within the same Python
    process. Separate Python processes would have to be created and coordinated
    in order to work around this limitation. Within the same process,
    `NotImplementedError` is raised if a client is already running.

    [1]: https://doc.comsol.com/6.0/doc/com.comsol.help.comsol/api\
/com/comsol/model/util/ModelUtil.html
    """

    version: str
    """Comsol version (e.g., `'6.0'`) the client is running on."""

    standalone: bool
    """Whether this is a stand-alone client or connected to a server."""

    port: int | None
    """Port number on which the client has connected to the server."""

    host: str | None
    """Host name or IP address of the server the client is connected to."""

    java: JClass
    """Java model object that this class instance is wrapped around."""

    ############
    # Internal #
    ############

    def __init__(self,
        cores:   int = None,
        version: str = None,
        port:    int = None,
        host:    str = 'localhost',
    ):

        # Make sure this is the one and only client.
        if jpype.isJVMStarted():
            error = 'Only one client can be instantiated per Python session.'
            log.error(error)
            raise NotImplementedError(error)

        # Discover Comsol back-end.
        backend = discovery.backend(version)

        # On Windows, turn off fault handlers if enabled.
        # Without this, pyTest will crash when starting the Java VM.
        # See "Errors reported by Python fault handler" in JPype docs.
        # The problem may be the SIGSEGV signal, see JPype issue #886.
        if discovery.system == 'Windows' and faulthandler.is_enabled():
            log.debug('Turning off Python fault handlers.')
            faulthandler.disable()

        # On Windows, prepend the JRE bin folder to the library search path.
        # See issue #49.
        if discovery.system == 'Windows':
            path = os.environ['PATH']
            jre  = backend['jvm'].parent.parent
            os.environ['PATH'] = str(jre) + os.pathsep + path

        # This is a stand-alone client if no port given.
        standalone = host and not port

        # Start the Java virtual machine.
        log.info('Starting Java virtual machine.')
        root = backend['root']
        args = [str(backend['jvm'])]
        if option('classkit'):
            args += ['-Dcs.ckl']
        log.debug(f'JVM arguments: {args}')
        if standalone:
            jpype.startJVM(*args, classpath=str(root/'plugins'/'*'))
        else:
            jpype.startJVM(*args, classpath=str(root/'apiplugins'/'*'))
        log.info('Java virtual machine has started.')

        # Import Comsol client object, a static class, i.e. singleton.
        # See `ModelUtil()` constructor in [1].
        from com.comsol.model.util import ModelUtil as java

        # Possibly initialize the stand-alone client.
        if standalone:
            log.info('Initializing stand-alone client.')

            # Instruct Comsol to limit number of processor cores to use.
            if cores:
                os.environ['COMSOL_NUM_THREADS'] = str(cores)

            # Initialize the environment with GUI support disabled.
            # See `initStandalone()` method in [1].
            java.initStandalone(False)

            # Load Comsol settings from disk so as to not just use defaults.
            # This is needed in stand-alone mode, see `loadPreferences()`
            # method in [1].
            java.loadPreferences()

            # Override certain settings not useful in headless operation.
            preferences = (
                ('updates.update.check', 'off'),
                ('tempfiles.saving.warnifoverwriteolder', 'off'),  # issue #50
                ('tempfiles.recovery.autosave', 'off'),
                ('tempfiles.recovery.checkforrecoveries', 'off'),  # issue #39
                ('tempfiles.saving.optimize', 'filesize'),
            )
            for (name, value) in preferences:
                try:
                    java.setPreference(name, value)
                except Exception:
                    log.info(f'Preference "{name}" does not exist.')

            # Log that we're done so the start-up time may be inspected.
            log.info('Stand-alone client initialized.')

        # Save instance attributes.
        self.version    = backend['name']
        self.standalone = standalone
        self.port       = None
        self.host       = None
        self.java       = java

        # Try to connect to server if not a stand-alone client.
        if not standalone and host and port is not None:
            self.connect(port, host)

    def __repr__(self) -> str:
        if self.standalone:
            connection = 'stand-alone'
        elif self.port:
            connection = f"port={self.port}, host='{self.host}'"
        else:
            connection = 'disconnected'
        return f'{self.__class__.__name__}({connection})'

    def __contains__(self, item: str | Model) -> bool:
        if isinstance(item, str) and item in self.names():
            return True
        if isinstance(item, Model) and item in self.models():
            return True
        return False

    def __iter__(self) -> Iterator[Model]:
        yield from self.models()

    def __truediv__(self, name: str) -> Model:
        if isinstance(name, str):
            for model in self:
                if name == model.name():
                    break
            else:
                error = f'Model "{name}" has not been loaded by client.'
                log.error(error)
                raise ValueError(error)
            return model
        return NotImplemented

    ##############
    # Inspection #
    ##############

    @property
    def cores(self) -> int:
        """Number of processor cores (threads) the Comsol session is using."""
        cores = self.java.getPreference('cluster.processor.numberofprocessors')
        cores = int(str(cores))
        return cores

    def models(self) -> list[Model]:
        """Returns all models currently held in memory."""
        return [Model(self.java.model(tag)) for tag in self.java.tags()]

    def names(self) -> list[str]:
        """Returns the names of all loaded models."""
        return [model.name() for model in self.models()]

    def files(self) -> list[Path]:
        """Returns the file-system paths of all loaded models."""
        return [model.file() for model in self.models()]

    def modules(self) -> list[str]:
        """Returns the names of available licensed modules/products."""
        names = []
        for (key, value) in modules.items():
            try:
                if self.java.hasProduct(key):
                    names.append(value)
            except Exception:
                pass
        return names

    ###############
    # Interaction #
    ###############

    def load(self, file: Path | str) -> Model:
        """Loads a model from the given `file` and returns it."""
        file = Path(file).resolve()
        if self.caching() and file in self.files():
            log.info(f'Retrieving "{file.name}" from cache.')
            return self.models()[self.files().index(file)]
        tag = self.java.uniquetag('model')
        log.info(f'Loading model "{file.name}".')
        model = Model(self.java.load(tag, str(file)))
        log.info('Finished loading model.')
        return model

    @overload
    def caching(self, state: None) -> bool: ...
    @overload
    def caching(self, state: bool): ...
    def caching(self, state=None):
        """
        Enables or disables caching of previously loaded models.

        Caching means that the [`load`](#Client.load) method will check if a
        model has been previously loaded from the same file-system path and,
        if so, return the in-memory model object instead of reloading it from
        disk. By default (at start-up) caching is disabled.

        Pass `True` to enable caching, `False` to disable it. If no argument is
        passed, the current state is returned.
        """
        if state is None:
            return option('caching')
        elif state in (True, False):
            option('caching', state)
        else:
            error = 'Caching state can only be set to either True or False.'
            log.error(error)
            raise ValueError(error)

    def create(self, name: str = None) -> Model:
        """
        Creates a new model and returns it as a [`Model`](#Model) instance.

        An optional `name` can be supplied. Otherwise the model will retain its
        automatically generated name, like "Model 1".
        """
        java = self.java.createUnique('model')
        model = Model(java)
        if name:
            model.rename(name)
        else:
            name = model.name()
        log.debug(f'Created model "{name}" with tag "{java.tag()}".')
        return model

    def remove(self, model: str | Model):
        """Removes the given [`model`](#Model) from memory."""
        if isinstance(model, str):
            if model not in self.names():
                error = f'No model named "{model}" exists.'
                log.error(error)
                raise ValueError(error)
            model = self/model
        elif isinstance(model, Model):
            try:
                model.java.tag()
            except Exception:
                error = 'Model does not exist.'
                log.error(error)
                raise ValueError(error) from None
            if model not in self.models():
                error = 'Model does not exist.'
                log.error(error)
                raise ValueError(error)
        else:
            error = 'Model must either be a model name or Model instance.'
            log.error(error)
            raise TypeError(error)
        name = model.name()
        tag  = model.java.tag()
        log.debug(f'Removing model "{name}" with tag "{tag}".')
        self.java.remove(tag)

    def clear(self):
        """Removes all loaded models from memory."""
        log.debug('Clearing all models from memory.')
        self.java.clear()

    ##########
    # Remote #
    ##########

    def connect(self, port: int, host: str = 'localhost'):
        """
        Connects the client to a server.

        The Comsol server must be listening at the given `port` for client
        connections. The `host` address defaults to `'localhost'`, but could be
        any domain name or IP address.

        This will fail for stand-alone clients or if the client is already
        connected to a server. In the latter case, call
        [`disconnect()`](#disconnect) first.
        """
        if self.standalone:
            error = 'Stand-alone clients cannot connect to a server.'
            log.error(error)
            raise RuntimeError(error)
        if self.port:
            error = 'Client already connected to a server. Disconnect first.'
            log.error(error)
            raise RuntimeError(error)
        log.info(f'Connecting to server "{host}" at port {port}.')
        self.java.connect(host, port)
        self.host = host
        self.port = port

    def disconnect(self):
        """
        Disconnects the client from the server.

        Note that the [`server`](#Server), unless started with the option
        `multi` set to `'on'`, will shut down as soon as the client
        disconnects.
        """
        if self.port:
            log.debug('Disconnecting from server.')
            self.java.disconnect()
            self.host = None
            self.port = None
        else:
            error = 'The client is not connected to a server.'
            log.error(error)
            raise RuntimeError(error)
