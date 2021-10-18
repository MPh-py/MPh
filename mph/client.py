"""Provides the wrapper for a Comsol client instance."""

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
import faulthandler                    # traceback dumps

########################################
# Globals                              #
########################################
log = getLogger(__package__)           # event log


########################################
# Constants                            #
########################################

# The following look-up table is used by the `modules()` method. It is
# based on the table on page 40 of Comsol 5.6's Programming Reference
# Manual, with the two columns swapped. It thus maps vendor strings to
# product names (add-on modules), except that we also shorten the names
# somewhat (drop "Module" everywhere) and leave out the pointless
# trademark symbols. The vendor strings are what we need to query the
# `ModelUtil.hasProduct()` Java method.

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
    'WAVEOPTICS':               'Wave Optics',
}


########################################
# Client                               #
########################################
class Client:
    """
    Manages the Comsol client instance.

    A client can either be a stand-alone instance or it could connect
    to a Comsol server started independently, possibly on a different
    machine on the network.

    Example usage:
    ```python
        import mph
        client = mph.Client(cores=1)
        model = client.load('model.mph')
        model.solve()
        model.save()
        client.remove(model)
    ```

    The number of `cores` (threads) the client instance uses can
    be restricted by specifying a number. Otherwise all available
    cores are used.

    A specific Comsol `version` can be selected if several are
    installed, for example `version='5.3a'`. Otherwise the latest
    version is used.

    Initializes a stand-alone Comsol session if no `port` number is
    specified. Otherwise tries to connect to the Comsol server
    listening at the given port for client connections. The `host`
    address defaults to `'localhost'`, but could be any domain name
    or IP address.

    This class is a wrapper around the [com.comsol.model.util.ModelUtil][1]
    Java class, which itself is wrapped by JPype and can be accessed
    directly via the `.java` attribute. The full Comsol functionality is
    thus available if needed.

    However, as that Comsol class is a singleton, i.e. a static class
    that cannot be instantiated, we can only run one client within the
    same Python process. Separate Python processes would have to be
    created and coordinated in order to work around this limitation.
    Within the same process, `NotImplementedError` is raised if a client
    is already running.

    [1]: https://doc.comsol.com/5.6/doc/com.comsol.help.comsol/api\
/com/comsol/model/util/ModelUtil.html
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, cores=None, version=None, port=None, host='localhost'):

        # Make sure this is the one and only client.
        if jpype.isJVMStarted():
            error = 'Only one client can be instantiated at a time.'
            log.error(error)
            raise NotImplementedError(error)

        # Discover Comsol back-end.
        backend = discovery.backend(version)

        # On Windows, turn off fault handlers if enabled.
        # Without this, pyTest will crash when starting the Java VM.
        # See "Errors reported by Python fault handler" in JPype docs.
        # The problem may be the SIGSEGV signal, see JPype issue #886.
        if platform.system() == 'Windows' and faulthandler.is_enabled():
            log.debug('Turning off Python fault handlers.')
            faulthandler.disable()

        # On Windows, prepend the Java folder to the library search path.
        # See issue #49.
        if platform.system() == 'Windows':
            path = os.environ['PATH']
            os.environ['PATH'] = str(backend['java']) + os.pathsep + path

        # Start the Java virtual machine.
        log.debug(f'JPype version is {jpype.__version__}.')
        log.info('Starting Java virtual machine.')
        root = backend['root']
        args = [str(backend['jvm'])]
        if option('classkit'):
            args += ['-Dcs.ckl']
        log.debug(f'JVM arguments: {args}')
        jpype.startJVM(*args, classpath=str(root/'plugins'/'*'))
        log.info('Java virtual machine has started.')

        # Import Comsol client object, a static class, i.e. singleton.
        # See `ModelUtil()` constructor in [1].
        from com.comsol.model.util import ModelUtil as java

        # This is a stand-alone client if no port given.
        standalone = host and not port

        # Possibly initialize the stand-alone client.
        if standalone:
            log.info('Initializing stand-alone client.')

            # Instruct Comsol to limit number of processor cores to use.
            if cores:
                os.environ['COMSOL_NUM_THREADS'] = str(cores)

            # Check correct setup of process environment if on Linux/macOS.
            check_environment(backend)

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
                ('tempfiles.saving.warnifoverwriteolder', 'off'), # issue #50
                ('tempfiles.recovery.autosave', 'off'),
                ('tempfiles.recovery.checkforrecoveries', 'off'), # issue #39
                ('tempfiles.saving.optimize', 'filesize'),
            )
            for (name, value) in preferences:
                try:
                    java.setPreference(name, value)
                except Exception:
                    log.info(f'Preference "{name}" does not exist.')

            # Log that we're done so the start-up time may be inspected.
            log.info('Stand-alone client initialized.')

        # Save and document instance attributes.
        # It seems to be necessary to document the instance attributes here
        # towards the end of the method. If done earlier, Sphinx would not
        # render them in source-code order, even though that's what we
        # request in the configuration. This might be a bug in Sphinx.
        self.version = backend['name']
        """Comsol version (e.g., `'5.3a'`) the client is running on."""
        self.standalone = standalone
        """Whether this is a stand-alone client or connected to a server."""
        self.port = None
        """Port number on which the client has connected to the server."""
        self.host = None
        """Host name or IP address of the server the client is connected to."""
        self.java = java
        """Java model object that this class instance is wrapped around."""

        # Try to connect to server if not a stand-alone client.
        if not standalone and host:
            self.connect(port, host)

    def __repr__(self):
        if self.standalone:
            connection = 'stand-alone'
        elif self.port:
            connection = f"port={self.port}, host='{self.host}'"
        else:
            connection = 'disconnected'
        return f'{self.__class__.__name__}({connection})'

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
                    break
            else:
                error = f'Model "{name}" has not been loaded by client.'
                log.error(error)
                raise ValueError(error)
            return model
        return NotImplemented

    ####################################
    # Inspection                       #
    ####################################

    @property
    def cores(self):
        """Number of processor cores (threads) the Comsol session is using."""
        cores = self.java.getPreference('cluster.processor.numberofprocessors')
        cores = int(str(cores))
        return cores

    def models(self):
        """Returns all models currently held in memory."""
        return [Model(self.java.model(tag)) for tag in self.java.tags()]

    def names(self):
        """Returns the names of all loaded models."""
        return [model.name() for model in self.models()]

    def files(self):
        """Returns the file-system paths of all loaded models."""
        return [model.file() for model in self.models()]

    def modules(self):
        """Returns the names of available licensed modules/products."""
        names = []
        for (key, value) in modules.items():
            try:
                if self.java.hasProduct(key):
                    names.append(value)
            except Exception:
                pass
        return names

    ####################################
    # Interaction                      #
    ####################################

    def load(self, file):
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
            log.error(error)
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
        log.debug(f'Created model "{name}" with tag "{java.tag()}".')
        return model

    def remove(self, model):
        """Removes the given `model` from memory."""
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

    ####################################
    # Remote                           #
    ####################################

    def connect(self, port, host='localhost'):
        """
        Connects the client to a server.

        The Comsol server must be listening at the given `port` for
        client connections. The `host` address defaults to `'localhost'`,
        but could be any domain name or IP address.

        This will fail for stand-alone clients or if the client is already
        connected to a server. In the latter case, `disconnect()` first.
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

        Note that the server, unless started with the option `multi`
        set to `'on'`, will shut down as soon as the client disconnects.
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
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        path = os.environ[var].split(os.pathsep)
        lib = root/'lib'/'glnxa64'
        if str(lib) not in path:
            error = f'Folder "{lib}" missing in library search path.'
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        gcc = root/'lib'/'glnxa64'/'gcc'
        if gcc.exists() and str(gcc) not in path:
            log.warning(f'Folder "{gcc}" missing in library search path.')
        gra = str(root/'ext'/'graphicsmagick'/'glnxa64')
        if str(gra) not in path:
            error = f'Folder "{gra}" missing in library search path.'
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        cad = root/'ext'/'cadimport'/'glnxa64'
        if cad.exists() and str(cad) not in path:
            log.warning(f'Folder "{cad}" missing in library search path.')
    elif system == 'Darwin':
        var = 'DYLD_LIBRARY_PATH'
        if var not in os.environ:
            error = f'Library search path {var} not set in environment.'
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        if var in os.environ:
            path = os.environ[var].split(os.pathsep)
        else:
            path = []
        lib = root/'lib'/'maci64'
        if str(lib) not in path:
            error = f'Folder "{lib}" missing in library search path.'
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        gra = root/'ext'/'graphicsmagick'/'maci64'
        if str(gra) not in path:
            error = f'Folder "{gra}" missing in library search path.'
            log.error(error)
            raise RuntimeError(error + '\n' + help)
        cad = root/'ext'/'cadimport'/'maci64'
        if cad.exists() and str(cad) not in path:
            log.warning(f'Folder "{cad}" missing in library search path.')
