"""Provides the wrapper for Comsol model objects."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import numpy                           # fast numerics
from numpy import array                # numerical array
from collections import namedtuple     # named tuples
import jpype.types as jtypes           # Java data types
from pathlib import Path               # file-system paths
from logging import getLogger          # event logging


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


########################################
# Model                                #
########################################
class Model:
    """
    Represents a Comsol model.

    This is a Python wrapper for the Comsol model's Java API. The
    class is not intended to be instantiated directly. Rather, the
    model would be loaded from a file by the client.

    Example:
    ```python
        import mph
        client = mph.start()
        model = client.load('capacitor.mph')
        model.parameter('U', '1', 'V')
        model.parameter('d', '1', 'mm')
        model.solve()
        C = model.evaluate('2*es.intWe/U^2', 'pF')
        print(f'capacitance C = {C:.3f} pF')
    ```

    The focus of the functionality exposed by this wrapper is to
    inspect an existing model, possibly change parameters, solve the
    model, then evaluate the results. The intention is *not* to create
    the model from scratch or to extensively modify its structure.
    Though if you wish to do that, just use the instance attribute
    `.java` to access the entire Comsol Java API from Python and refer
    to the Comsol Programming Manual for guidance.

    The `parent` argument to the constructor is usually that internal
    Java object around which this class here is wrapped. But in order
    to simplify extending the class with custom functionality, the
    constructor also accepts instances of this class or a child class.
    In that case, it will preserve the original `.java` object throughout
    the class hierarchy so that you can simply "type-cast" an existing
    `Model` instance (as loaded by the client) to a derived child class.
    """

    def __init__(self, parent):
        if isinstance(parent, Model):
            self.java = parent.java
        else:
            self.java = parent

        # This dict holds the names to access the subgroups in the java object
        # I chose plural here since it reads better, however comsol chooses
        # a mix of singular and acronyms. By intent, those are the callables
        # so access to subfeatures is possbile
        self._groups = {'functions': self.java.func,
                        'solutions': self.java.sol,
                        'results':   self.java.result,
                        'datasets':  self.java.result().dataset,
                        'exports':   self.java.result().export,
                        }

    # Internal access
    def _group(self, name):
        try:
            return self._groups[name]
        except KeyError:
            logger.error(f'The group {name} is not implemented yet.')
            return None

    def __eq__(self, other):
        return self.java.tag() == other.java.tag()

    ####################################
    # Inspection                       #
    ####################################
    def groups(self):
        return [k for k in self._groups.keys()]

    def name(self):
        """Returns the model's name."""
        name = str(self.java.name())
        if name.endswith('.mph'):
            name = name.rsplit('.', maxsplit=1)[0]
        return name

    def file(self):
        """Returns the absolute path to the file the model was loaded from."""
        return Path(str(self.java.getFilePath())).resolve()

    def parameters(self):
        """
        Returns the global model parameters.

        The parameters are returned as a list of tuples holding name,
        value, and description for each of them.
        """
        Parameter = namedtuple('parameter', ('name', 'value', 'description'))
        parameters = []
        for name in self.java.param().varnames():
            name  = str(name)
            value = str(self.java.param().get(name))
            descr = str(self.java.param().descr(name))
            parameters.append(Parameter(name, value, descr))
        return parameters

    def functions(self):
        """Returns the names of all globally defined functions."""
        tags = [tag for tag in self.java.func().tags()]
        return [str(self.java.func(tag).name()) for tag in tags]

    def components(self):
        """Returns the names of all model components."""
        tags = [tag for tag in self.java.component().tags()]
        return [str(self.java.component(tag).name()) for tag in tags]

    def geometries(self):
        """Returns the names of all geometry sequences."""
        tags = [tag for tag in self.java.geom().tags()]
        return [str(self.java.geom(tag).name()) for tag in tags]

    def selections(self):
        """Returns the names of all selections."""
        tags = [tag for tag in self.java.selection().tags()]
        return [str(self.java.selection(tag).name()) for tag in tags]

    def physics(self):
        """Returns the names of all physics interfaces."""
        tags = [tag for tag in self.java.physics().tags()]
        return [str(self.java.physics(tag).name()) for tag in tags]

    def features(self, physics):
        """
        Returns the names of all features in the given `physics` interface.

        The term feature refers to the nodes defined under a physics
        interface. They define the differential equations, boundary
        conditions, initial values, etc.
        """
        if physics not in self.physics():
            error = f'No physics interface named "{physics}".'
            logger.critical(error)
            raise LookupError(error)
        tags = [tag for tag in self.java.physics().tags()]
        ptag = tags[self.physics().index(physics)]
        tags = [tag for tag in self.java.physics(ptag).feature().tags()]
        return [str(self.java.physics(ptag).feature(ftag).name())
                for ftag in tags]

    def materials(self):
        """Returns the names of all materials."""
        tags = [tag for tag in self.java.material().tags()]
        return [str(self.java.material(tag).name()) for tag in tags]

    def meshes(self):
        """Returns the names of all mesh sequences."""
        tags = [tag for tag in self.java.mesh().tags()]
        return [str(self.java.mesh(tag).name()) for tag in tags]

    def studies(self):
        """Returns the names of all studies."""
        tags = [tag for tag in self.java.study().tags()]
        return [str(self.java.study(tag).name()) for tag in tags]

    def solutions(self):
        """Returns the names of all solutions."""
        tags = [tag for tag in self.java.sol().tags()]
        return [str(self.java.sol(tag).name()) for tag in tags]

    def datasets(self):
        """Returns the names of all datasets."""
        tags = [tag for tag in self.java.result().dataset().tags()]
        return [str(self.java.result().dataset(tag).name()) for tag in tags]

    def plots(self):
        """Returns the names of all plots."""
        tags = [tag for tag in self.java.result().tags()]
        return [str(self.java.result(tag).name()) for tag in tags]

    def exports(self):
        """Returns the names of all exports."""
        tags = [tag for tag in self.java.result().export().tags()]
        return [str(self.java.result().export(tag).name()) for tag in tags]

    ####################################
    # Interaction                      #
    ####################################

    def rename(self, name):
        """Assigns a new `name` to the model."""
        self.java.name(name)

    def parameter(self, name, value=None, unit=None, description=None,
                  evaluate=False):
        """
        Returns or sets the parameter of the given `name`.

        If no `value` is given (the default `None` is passed), returns
        the value of the named parameter. Otherwise sets it.

        Values are accepted as expressions (strings) or as numerical
        values (referring to default units). An optional `unit` may be
        specified, unless it is already part of the expression itself,
        inside square brackets.

        By default, values are always returned as strings, i.e. the
        expression as entered in the user interface. That expression
        may include the unit, again inside brackets. If the option
        `evaluate` is set to `True`, the numerical value that the
        parameter expression evaluate to is returned.

        A parameter `description` can be supplied and will be set
        regardless of a value being passed or not.
        """
        if description is not None:
            value = self.parameter(name)
            self.java.param().set(name, value, description)
        if value is None:
            if not evaluate:
                return str(self.java.param().get(name))
            else:
                return self.java.param().evaluate(name)
        else:
            value = str(value)
            if unit:
                value += f' [{unit}]'
            self.java.param().set(name, value)

    def load(self, file, interpolation):
        """
        Loads an external `file` and assigns its data to the named
        `interpolation` function.
        """
        for tag in self.java.func().tags():
            if str(self.java.func(tag).label()) == interpolation:
                break
        else:
            error = f'Interpolation function "{interpolation}" does not exist.'
            logger.critical(error)
            raise LookupError(error)
        file = Path(file)
        logger.info(f'Loading external data from file "{file.name}".')
        self.java.func(tag).discardData()
        self.java.func(tag).set('filename', f'{file}')
        self.java.func(tag).importData()
        logger.info('Finished loading external data.')

    # Changed type to feature to not shadow internal type
    def create(self, group, feature, name):
        # This will raise an exception if feature is not possible for given
        # group. We could hardcode that out or just handle the exception.
        # Latter is simpler I guess. Using the access method creates a clear
        # KeyError on missing group
        group = self._group(group)
        if group is None:
            return

        utag = group().uniquetag(f'{feature.lower()}')
        try:
            group().create(utag, feature)
            group(utag).label(name)
        except Exception:
            # This will say something like "cannot be created in this context"
            # Is this clear enough?
            logger.exception(f'Could not create feature {feature} in group {group}')

    # This could replace _dataset and _solution
    def _node(self, group, name):
        group = self._group(group)
        if group is None:
            return None

        tags = [tag for tag in group().tags()]
        names = [str(group(tag).name()) for tag in tags]
        try:
            feature = group(tags[names.index(name)])
        except ValueError:
            logger.error(f'Feature {name} does not exist')
            return None

        return feature

    def property(self, group, name, **kwargs):
        feature = self._node(group, name)
        if feature is None:
            return

        output = dict()
        for prop, value in kwargs.items():
            if value is None:
                logger.info(f'Reading feature property {prop}')
                # This is problematic since COMSOL uses get* to typecase. Since
                # this is only for reading / printing, getString() seems to work
                # universally if the type is not array. In this case a simple
                # catch is tried
                try:
                    output[prop] = feature.getString(prop)
                except Exception:
                    try:
                        # A String matrix catches the rest
                        output[prop] = array(
                            [[col for col in row]
                             for row in feature.getStringMatrix(prop)],
                            dtype=object)

                    except Exception:
                        logger.exception(f'Cannot read feature property {prop}')
            else:
                logger.info(f'Setting feature property {prop}')
                try:
                    # Some basic typecasting is needed here
                    if isinstance(value, int):
                        value = jtypes.JInt(value)
                    elif isinstance(value, float):
                        value = jtypes.JDouble(float)
                    elif isinstance(value, bool):
                        value = jtypes.JBoolean(value)

                    feature.set(prop, value)
                    output[prop] = feature.getString(prop)
                except Exception:
                    # more traceback since this might be due to missing
                    # property or more complex type errors
                    logger.exception(f'Cannot set feature property {prop}')

        return output

    def properties(self, group, name):
        feature = self._node(group, name)
        if feature is None:
            return

        return [s for s in feature.properties()]

    def remove(self, group, name):
        tag = self._node(group, name).tag()
        group = self._group(group)()
        if group is None:
            return
        group.remove(tag)

    def toggle(self, physics, feature, action='flip'):
        """
        Enables or disables features of a physics interface.

        If `action` is `'flip'` (the default), it enables the feature
        if it is currently disabled or disables it if enabled. Pass
        `'enable'` or `'on'` to enable the feature regardless of its
        current state. Pass `'disable'` or `'off'` to disable it.
        """
        if physics not in self.physics():
            error = f'No physics interface named "{physics}".'
            logger.critical(error)
            raise LookupError(error)
        tags = [tag for tag in self.java.physics().tags()]
        ptag = tags[self.physics().index(physics)]
        node = self.java.physics(ptag)
        if feature not in self.features(physics):
            error = f'No feature named "{feature}" in physics "{physics}".'
            logger.critical(error)
            raise LookupError(error)
        tags = [tag for tag in node.feature().tags()]
        ftag = tags[self.features(physics).index(feature)]
        node = node.feature(ftag)
        if action == 'flip':
            node.active(not node.isActive())
        elif action in ('enable', 'on', 'activate'):
            node.active(True)
        elif action in ('disable', 'off', 'deactivate'):
            node.active(False)

    ####################################
    # Solving                          #
    ####################################

    def build(self, geometry=None):
        """Builds the named `geometry`, or all of them if none given."""
        tags  = [tag for tag in self.java.geom().tags()]
        names = self.geometries()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if geometry is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == geometry}
            if not index:
                error = f'Geometry sequence "{geometry}" does not exist.'
                logger.critical(error)
                raise LookupError(error)
        elif not index:
            error = 'No geometry sequence defined in the model tree.'
            logger.critical(error)
            raise RuntimeError(error)
        for (name, tag) in index.items():
            logger.info(f'Running geometry sequence "{name}".')
            self.java.geom(tag).run()
            logger.info('Finished geometry sequence.')

    def mesh(self, mesh=None):
        """Runs the named `mesh` sequence, or all of them if none given."""
        tags  = [tag for tag in self.java.mesh().tags()]
        names = self.meshes()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if mesh is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == mesh}
            if not index:
                error = f'Mesh sequence "{mesh}" does not exist.'
                logger.critical(error)
                raise LookupError(error)
        elif not index:
            error = 'No mesh sequence defined in the model tree.'
            logger.critical(error)
            raise RuntimeError(error)
        for (name, tag) in index.items():
            logger.info(f'Running mesh sequence "{name}".')
            self.java.mesh(tag).run()
            logger.info('Finished mesh sequence.')

    def solve(self, study=None):
        """Solves the named `study`, or all of them if none given."""
        tags  = [tag for tag in self.java.study().tags()]
        names = self.studies()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if study is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == study}
            if not index:
                error = f'Study "{study}" does not exist.'
                logger.critical(error)
                raise LookupError(error)
        elif not index:
            error = 'No study defined in the model tree.'
            logger.critical(error)
            raise RuntimeError(error)
        for (name, tag) in index.items():
            logger.info(f'Running study "{name}".')
            self.java.study(tag).run()
            logger.info('Finished solving study.')

    ####################################
    # Evaluation                       #
    ####################################

    def _dataset(self, name=None):
        """
        Returns the Java dataset object.

        If `name` is given, returns the dataset object with that name.
        Otherwise returns the default dataset.
        """
        if name is not None:
            names = self.datasets()
            tags  = [tag for tag in self.java.result().dataset().tags()]
            try:
                dtag = tags[names.index(name)]
            except ValueError:
                error = f'Dataset "{name}" does not exist.'
                raise LookupError(error) from None
        else:
            etag = self.java.result().numerical().uniquetag('eval')
            eval = self.java.result().numerical().create(etag, 'Eval')
            dtag = eval.getString('data')
            self.java.result().numerical().remove(etag)
        return self.java.result().dataset(dtag)

    def _solution(self, dataset=None):
        """Returns the Java solution object the named `dataset` is based on."""
        dset = self._dataset(dataset)
        stag = dset.getString('solution')
        return self.java.sol(stag)

    def inner(self, dataset=None):
        """
        Returns the indices and values of inner solutions.

        These are the solution indices and time values in
        time-dependent studies, returned as a tuple of an integer
        array and a floating-point array. A `dataset` name may be
        specified. Otherwise the default dataset is used.
        """
        dataset  = self._dataset(dataset)
        solution = self._solution(dataset.name())
        solinfo  = solution.getSolutioninfo()
        indices  = array(solinfo.getSolnum(1, True))
        values   = array(solution.getPVals())
        return (indices, values)

    def outer(self, dataset=None):
        """
        Returns the indices and values of outer solutions.

        These are the solution indices and values in parametric sweeps,
        returned as a tuple of an integer array and a floating-point
        array. A `dataset` name may be specified. Otherwise the default
        dataset is used.
        """
        dataset  = self._dataset(dataset)
        solution = self._solution(dataset.name())
        solinfo  = solution.getSolutioninfo()
        indices  = array(solinfo.getOuterSolnum())
        values   = array([solinfo.getPvals([[index,1]])[0][0]
                          for index in indices])
        return (indices, values)

    def evaluate(self, expression, unit=None, dataset=None,
                       inner=None, outer=None):
        """
        Evaluates an expression and returns the numerical results.

        The `expression` may be a string, denoting a single expression,
        or a sequence of strings, denoting multiple. The optional
        `unit` must be given correspondingly. If omitted, default
        units are used.

        A `dataset` may be specified. Otherwise the expression will
        be evaluated on the default dataset. If the solution stored in
        the dataset is time-dependent, one or several `inner`
        solution(s) can be preselected, either by an index number, a
        sequence of indices, or by passing "first"/"last" to select
        the very first/last index. If the dataset represents a
        parameter sweep, the `outer` solution(s) can be selected by
        index or sequence of indices.

        Results are returned as NumPy arrays of whichever
        dimensionality they may have. The expression may be a global
        one, or a scalar field, or particle data.
        """

        # Get dataset and solution (Java) objects.
        dataset = self._dataset(dataset)
        logger.info(f'Evaluating {expression} on "{dataset.name()}" dataset.')
        solution = self._solution(dataset.name())

        # Make sure solution has actually been computed.
        if solution.isEmpty():
            error = 'The solution has not been computed.'
            logger.critical(error)
            raise RuntimeError(error)

        # Validate solution arguments.
        if not (inner is None
                or (isinstance(inner, str)
                    and inner in ('first', 'last'))
                or (isinstance(inner, list)
                    and all(isinstance(index, int) for index in inner))
                or (isinstance(inner, numpy.ndarray)
                    and inner.dtype == 'int')):
            error = ('Argument "inner", if specified, must be either '
                     '"first", "last", or a list/array of integers.')
            logger.critical(error)
            raise ValueError(error)
        if not (outer is None
                or isinstance(outer, int)
                or (hasattr(outer, 'dtype')
                    and issubclass(outer.dtype.type, numpy.integer)
                    and not outer.shape)):
            error = 'Argument "outer", if specified, must be an integer index.'
            logger.critical(error)
            raise ValueError(error)

        # Try to perform a global evaluation, which may fail.
        etag = self.java.result().numerical().uniquetag('eval')
        eval = self.java.result().numerical().create(etag, 'Global')
        eval.set('expr', expression)
        if unit is not None:
            eval.set('unit', unit)
        if dataset is not None:
            eval.set('data', dataset.tag())
        if outer is not None:
            eval.set('outersolnum', jtypes.JInt(outer))
        try:
            logger.info('Trying global evaluation.')
            results = array(eval.getData())
            if eval.isComplex():
                results += 1j * array(eval.getImagData())
            self.java.result().numerical().remove(etag)
            logger.info('Finished global evaluation.')
            if inner is None:
                pass
            elif inner == 'first':
                results = results[:, 0, :]
            elif inner == 'last':
                results = results[:, -1, :]
            else:
                results = results[:, inner, :]
            return results.squeeze()
        # Move on if this fails. It seems to not be a global expression then.
        except Exception:
            logger.info('Global evaluation failed.')

        # Find out the type of the dataset.
        dtype = str(dataset.getType()).lower()

        # For particle datasets, create an EvalPoint node.
        etag = self.java.result().numerical().uniquetag('eval')
        if dtype == 'particle':
            eval = self.java.result().numerical().create(etag, 'EvalPoint')
            if inner is not None:
                if inner in ('first', 'last'):
                    eval.set('innerinput', inner)
                else:
                    eval.set('innerinput', 'manual')
                    eval.set('solnum', [jtypes.JInt(index) for index in inner])
        # Otherwise create an Eval node.
        else:
            eval = self.java.result().numerical().create(etag, 'Eval')

        # Select the dataset, if specified.
        if dataset is not None:
            eval.set('data', dataset.tag())

        # Set the expression(s) to be evaluated.
        eval.set('expr', expression)

        # Set the unit(s), if specified.
        if unit is not None:
            eval.set('unit', unit)

        # Select an outer solution, i.e. parameter index, if specified.
        if outer is not None:
            eval.set('outersolnum', jtypes.JInt(outer))

        # Retrieve the data.
        logger.info('Retrieving data.')
        if dtype == 'particle':
            results = array(eval.getReal())
            if eval.isComplex():
                results += 1j * array(eval.getImag())
            if isinstance(expression, (tuple, list)):
                shape = results.shape[1:]
                results = results.reshape(len(expression), -1, *shape)
        else:
            results = array(eval.getData())
            if eval.isComplex():
                results += 1j * array(eval.getImagData())
            if inner is None:
                pass
            elif inner == 'first':
                results = results[:, 0, :]
            elif inner == 'last':
                results = results[:, -1, :]
            else:
                results = results[:, inner, :]
        logger.info('Finished retrieving data.')

        # Remove the temporary evaluation node we added to the model.
        self.java.result().numerical().remove(etag)

        # Squeeze out singleton array dimensions.
        results = results.squeeze()

        # Return array of results.
        return results

    ####################################
    # Files                            #
    ####################################

    def export(self, node, file=None):
        """
        Runs the named export `node`.

        A `file` name can be specified. Otherwise the file name defined
        in the export node itself will be used.
        """
        names   = self.exports()
        tags    = [tag for tag in self.java.result().export().tags()]
        tag     = tags[names.index(node)]
        feature = self.java.result().export(tag)
        if file is not None:
            feature.set('filename', str(file))
        feature.run()

    def clear(self):
        """Clears stored solution, mesh, and plot data."""
        logger.info('Clearing stored plot data.')
        self.java.result().clearStoredPlotData()
        logger.info('Finished clearing plots.')
        logger.info('Clearing solution data.')
        for tag in self.java.sol().tags():
            self.java.sol(tag).clearSolution()
        logger.info('Finished clearing solutions.')
        logger.info('Clearing mesh data.')
        for tag in self.java.mesh().tags():
            self.java.mesh(tag).clearMesh()
        logger.info('Finished clearing meshes.')

    def reset(self):
        """Resets the modeling history."""
        logger.info('Resetting modeling history.')
        self.java.resetHist()
        logger.info('Finished resetting history.')

    def save(self, path=None, format=None):
        """
        Saves the model at the given file-system `path`.

        If `path` is not given, the original file name is used, i.e.
        the one from which the model was loaded to begin with. If
        the path contains no folder information, the current folder
        (working directory) is used. If the path points to a folder,
        the model name is used to name the file inside that folder.

        A `format` can be specified as either "Comsol", "Java",
        "Matlab", or "VBA". If no format is given, it will be deduced
        from the file's ending, being either `.mph`, `.java`, `.m`, or
        `.vba`, respectively. No file ending implies "Comsol" format.

        Imposes the correct file ending for the format. Overwrites
        existing files.
        """

        # Possibly deduce format from file ending.
        if format is None:
            suffix = path.suffix if path else '.mph'
            if suffix in ('.mph', ''):
                format = 'Comsol'
            elif suffix == '.java':
                format = 'Java'
            elif suffix == '.m':
                format = 'Matlab'
            elif suffix == '.vba':
                format = 'VBA'
            else:
                error = f'Cannot deduce file format from ending "{suffix}".'
                logger.critical(error)
                raise ValueError(error)

        # Allow synonyms for format and map to Comsol's file type.
        if format in ('Comsol', 'mph', '.mph'):
            (format, type) = ('Comsol', 'mph')
        elif format in ('Java', 'java', '.java'):
            (format, type) = ('Java', 'java')
        elif format in ('Matlab', 'm', '.m'):
            (format, type) = ('Matlab', 'm')
        elif format in ('VBA', 'vba', '.vba'):
            (format, type) = ('VBA', 'vba')
        else:
            error = f'Invalid file format "{format}".'
            logger.critical(error)
            raise ValueError(error)

        # Use model name if no file name specified.
        if path is None:
            if format == 'Comsol':
                logger.info(f'Saving model "{self.name()}".')
                self.java.save()
            else:
                file = self.name() + '.' + type
                logger.info(f'Saving model as "{file.name}".')
                self.java.save(str(file), type)
        # Otherwise save at given path.
        else:
            if isinstance(path, str):
                path = Path.cwd()/path
            if path.is_dir():
                file = (path/self.name()).with_suffix(f'.{type}')
            else:
                file = path.with_suffix(f'.{type}')
            logger.info(f'Saving model as "{file.name}".')
            if format == 'Comsol':
                self.java.save(str(file))
            else:
                self.java.save(str(file), type)
        logger.info('Finished saving model.')
