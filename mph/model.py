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
logger = getLogger(__package__)        # package-wide event logger


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
        client = mph.Client()
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
    """

    def __init__(self, java):
        self.java = java

    ####################################
    # Inspection                       #
    ####################################

    def name(self):
        """Returns the model's name."""
        name = str(self.java.name())
        if name.endswith('.mph'):
            name = name.rsplit('.', maxsplit=1)[0]
        return name

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
        tags = [str(tag) for tag in self.java.func().tags()]
        return [str(self.java.func(tag).name()) for tag in tags]

    def components(self):
        """Returns the names of all model components."""
        tags = [str(tag) for tag in self.java.component().tags()]
        return [str(self.java.component(tag).name()) for tag in tags]

    def geometries(self):
        """Returns the names of all geometry sequences."""
        tags = [str(tag) for tag in self.java.geom().tags()]
        return [str(self.java.geom(tag).name()) for tag in tags]

    def physics(self):
        """Returns the names of all physics interfaces."""
        tags = [str(tag) for tag in self.java.physics().tags()]
        return [str(self.java.physics(tag).name()) for tag in tags]

    def materials(self):
        """Returns the names of all materials."""
        tags = [str(tag) for tag in self.java.material().tags()]
        return [str(self.java.material(tag).name()) for tag in tags]

    def meshes(self):
        """Returns the names of all mesh sequences."""
        tags = [str(tag) for tag in self.java.mesh().tags()]
        return [str(self.java.mesh(tag).name()) for tag in tags]

    def studies(self):
        """Returns the names of all studies."""
        tags = [str(tag) for tag in self.java.study().tags()]
        return [str(self.java.study(tag).name()) for tag in tags]

    def solutions(self):
        """Returns the names of all solutions."""
        tags = [str(tag) for tag in self.java.sol().tags()]
        return [str(self.java.sol(tag).name()) for tag in tags]

    def datasets(self):
        """Returns the names of all datasets."""
        tags = [str(tag) for tag in self.java.result().dataset().tags()]
        return [str(self.java.result().dataset(tag).name()) for tag in tags]

    def plots(self):
        """Returns the names of all plots."""
        tags = [str(tag) for tag in self.java.result().tags()]
        return [str(self.java.result(tag).name()) for tag in tags]

    def exports(self):
        """Returns the names of all exports."""
        tags = [str(tag) for tag in self.java.result().export().tags()]
        return [str(self.java.result().export(tag).name()) for tag in tags]

    ####################################
    # Interaction                      #
    ####################################

    def rename(self, name):
        """Assigns a new `name` to the model."""
        self.java.name(name)

    def parameter(self, name, value=None, unit=None):
        """
        Returns or sets the parameter of the given `name`.

        If no `value` is given (the default `None` is passed), returns
        the value of the named parameter. Otherwise sets it.

        Numerical values are accepted, but will be converted to strings.
        An optional `unit` may be specified, unless it is already part
        of the value string itself, inside square brackets.

        Values are always returned as strings, i.e. the expression as
        entered in the user interface. That expression may include the
        unit, again inside brackets.
        """
        if value is None:
            return str(self.java.param().get(name))
        else:
            value = str(value)
            if unit:
                value += f'[{unit}]'
            self.java.param().set(name, value)

    def load(self, file, interpolation):
        """
        Loads an external `file` and assigns its data to the named
        `interpolation` function.
        """
        for tag in self.java.func().tags():
            tag = str(tag)
            if str(self.java.func(tag).label()) == interpolation:
                break
        else:
            error = f'Interpolation function "{interpolation}" does not exist.'
            logger.error(error)
            raise ValueError(error)
        file = Path(file)
        logger.info(f'Loading external data from file "{file.name}".')
        self.java.func(tag).discardData()
        self.java.func(tag).set('filename', f'{file}')
        self.java.func(tag).importData()
        logger.info('Finished loading external data.')

    ####################################
    # Solving                          #
    ####################################

    def build(self, geometry=None):
        """Builds the named `geometry`, or all of them if none given."""
        tags  = [str(tag) for tag in self.java.geom().tags()]
        names = self.geometries()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if geometry is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == geometry}
            if not index:
                error = f'Geometry sequence "{geometry}" does not exist.'
                logger.error(error)
                raise ValueError(error)
        elif not index:
            error = 'No geometry sequence defined in the model tree.'
            logger.error(error)
            raise RuntimeError(error)
        for (name, tag) in index.items():
            logger.info(f'Running geometry sequence "{name}".')
            self.java.geom(tag).run()
            logger.info('Finished geometry sequence.')

    def mesh(self, mesh=None):
        """Runs the named `mesh` sequence, or all of them if none given."""
        tags  = [str(tag) for tag in self.java.mesh().tags()]
        names = self.meshes()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if mesh is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == mesh}
            if not index:
                error = f'Mesh sequence "{mesh}" does not exist.'
                logger.error(error)
                raise ValueError(error)
        elif not index:
            error = 'No mesh sequence defined in the model tree.'
            logger.error(error)
            raise RuntimeError(error)
        for (name, tag) in index.items():
            logger.info(f'Running mesh sequence "{name}".')
            self.java.mesh(tag).run()
            logger.info('Finished mesh sequence.')

    def solve(self, study=None):
        """Solves the named `study`, or all of them if none given."""
        tags  = [str(tag) for tag in self.java.study().tags()]
        names = self.studies()
        index = {name: tag for (tag, name) in zip(tags, names)}
        if study is not None:
            index = {name: tag for (name, tag) in index.items()
                     if name == study}
            if not index:
                error = f'Study "{study}" does not exist.'
                logger.error(error)
                raise ValueError(error)
        elif not index:
            error = 'No study defined in the model tree.'
            logger.error(error)
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
                raise ValueError(error) from None
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
        one, or a scalar field, or particle data. `ValueError`
        exceptions are raised if anything goes wrong, such as the
        solution not having been computed.
        """

        # Get dataset and solution (Java) objects.
        dataset = self._dataset(dataset)
        logger.info(f'Evaluating {expression} on "{dataset.name()}" dataset.')
        solution = self._solution(dataset.name())

        # Make sure solution has actually been computed.
        if solution.isEmpty():
            error = 'The solution has not been computed.'
            logger.error(error)
            raise ValueError(error)

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
            logger.error(error)
            raise ValueError(error)
        if not (outer is None
                or isinstance(outer, int)
                or (hasattr(outer, 'dtype')
                    and issubclass(outer.dtype.type, numpy.integer)
                    and not outer.shape)):
            error = 'Argument "outer", if specified, must be an integer index.'
            logger.error(error)
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
        tags    = [str(tag) for tag in self.java.result().export().tags()]
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

    def save(self, path=None):
        """
        Saves the model at the given file-system `path`.

        If `path` is not given, the original file name is used, i.e.
        the one from which the model was loaded to begin with. If
        `path` contains no directory information, the current folder
        (working directory) is used. If `path` points to a directory,
        the model name is used to name the file inside that directory.

        Overwrites existing files. Imposes a `.mph` file ending.
        """
        if path is None:
            logger.info(f'Saving model "{self.name()}".')
            self.java.save()
        else:
            name = self.name()
            if isinstance(path, str):
                path = Path.cwd()/path
            if path.is_dir():
                path = path/name
            if not path.name.endswith('.mph'):
                path = path.with_name(path.name + '.mph')
            logger.info(f'Saving model as "{path}".')
            self.java.save(str(path))
            self.rename(name)
        logger.info('Finished saving model.')
