"""Provides the wrapper for Comsol model objects."""

########################################
# Components                           #
########################################
from .node import Node                 # model node

########################################
# Dependencies                         #
########################################
from numpy import array, ndarray       # numerical array
from numpy import integer              # NumPy integer
from pathlib import Path               # file-system path
from re import match                   # pattern matching
from warnings import warn              # user warning
from logging import getLogger          # event logging

########################################
# Globals                              #
########################################
log = getLogger(__package__)           # event log

########################################
# Constants                            #
########################################

# The following look-up table is used by the `modules()` method. It maps
# the product names (add-on modules) returned by `model.getUsedProducts()`
# to the same sanitized names used in the look-up table in the `clients`
# module. So it essentially drops the Unicode trademark symbols as well
# as the redundant "Module". The strings returned by `getUsedProducts()`
# seem to correspond exactly to the product names in the left column
# of the table on page 40 of Comsol 5.6's Programming Reference Manual.

modules = {
    'AC/DC Module':                          'AC/DC',
    'Acoustics Module':                      'Acoustics',
    'Battery Design Module':                 'Battery Design',
    'CAD Import Module':                     'CAD Import',
    'CFD Module':                            'CFD',
    'COMSOL Multiphysics':                   'Comsol core',
    'Chemical Reaction Engineering Module':  'Chemical Reaction Engineering',
    'Cluster Computing Module':              'Cluster Computing',
    'Composite Materials Module':            'Composite Materials',
    'Corrosion Module':                      'Corrosion',
    'Design Module':                         'Design',
    'ECAD Import Module':                    'ECAD Import',
    'Electrochemistry Module':               'Electrochemistry',
    'Electrodeposition Module':              'Electrodeposition',
    'Fatigue Module':                        'Fatigue',
    'File Import for CATIA V5':              'File Import for Catia v5',
    'Fuel Cell & Electrolyzer Module':       'Fuel Cell & Electrolyzer',
    'Geomechanics Module':                   'Geomechanics',
    'Heat Transfer Module':                  'Heat Transfer',
    'Liquid & Gas Properties Module':        'Liquid & Gas Properties',
    'LiveLink™ for AutoCAD®':                'LiveLink AutoCAD',
    'LiveLink™ for PTC® Creo® Parametric™':  'LiveLink PTC Creo Parametric',
    'LiveLink™ for Excel®':                  'LiveLink Excel',
    'LiveLink™ for Inventor®':               'LiveLink Inventor',
    'LiveLink™ for MATLAB®':                 'LiveLink Matlab',
    'LiveLink™ for Revit®':                  'LiveLink Revit',
    'LiveLink™ for PTC® Pro/ENGINEER®':      'LiveLink PTC Pro/ENGINEER',
    'LiveLink™ for Solid Edge®':             'LiveLink Solid Edge',
    'LiveLink™ for SOLIDWORKS®':             'LiveLink SolidWorks',
    'MEMS Module':                           'MEMS',
    'Microfluidics Module':                  'Microfluidics',
    'Mixer Module':                          'Mixer',
    'Molecular Flow Module':                 'Molecular Flow',
    'Multibody Dynamics Module':             'Multibody Dynamics',
    'Nonlinear Structural Materials Module': 'Nonlinear Structural Materials',
    'Optimization Module':                   'Optimization',
    'Particle Tracing Module':               'Particle Tracing',
    'Pipe Flow Module':                      'Pipe Flow',
    'Plasma Module':                         'Plasma',
    'Polymer Flow Module':                   'Polymer Flow',
    'Ray Optics Module':                     'Ray Optics',
    'RF Module':                             'RF',
    'Rotordynamics Module':                  'Rotordynamics',
    'Semiconductor Module':                  'Semiconductor',
    'Structural Mechanics Module':           'Structural Mechanics',
    'Subsurface Flow Module':                'Subsurface Flow',
    'Wave Optics Module':                    'Wave Optics',
}


########################################
# Model                                #
########################################
class Model:
    """
    Represents a Comsol model.

    The class is not intended to be instantiated directly. Rather, the
    model would be loaded from a file by the client.

    Example usage:
    ```python
        import mph
        client = mph.start()
        model = client.load('capacitor.mph')
        model.parameter('U', '1 [V]')
        model.parameter('d', '1 [mm]')
        model.solve()
        C = model.evaluate('2*es.intWe/U^2', 'pF')
        print(f'capacitance C = {C:.3f} pF')
    ```

    The focus of the functionality exposed by this class is to
    inspect an existing model, possibly change parameters, solve the
    model, then evaluate the results. The intention is not *per se*
    to create the model from scratch or to extensively modify its
    structure, though some such functionality is offered here, and
    even more of it through the `Node` class.

    This class is a wrapper around the [com.comsol.model.Model][1]
    Java class, which itself is wrapped by JPype and can be accessed
    directly via the `.java` attribute. The full Comsol functionality is
    thus available if needed.

    The `parent` argument to the constructor is usually that internal
    Java object. But in order to simplify extending the class with
    custom functionality, the constructor also accepts instances of
    this very class or a child class. In that case, it will preserve
    the original `.java` reference throughout the class hierarchy so
    that it is possible to "type-cast" an existing `Model` instance
    (as loaded by the client) to a derived child class.

    [1]: https://doc.comsol.com/5.6/doc/com.comsol.help.comsol/api\
/com/comsol/model/Model.html
    """

    ####################################
    # Internal                         #
    ####################################

    def __init__(self, parent):
        if isinstance(parent, Model):
            java = parent.java
        else:
            java = parent
        self.java = java
        """Java object that this instance is wrapped around."""

    def __str__(self):
        return self.name()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __eq__(self, other):
        return self.java.tag() == other.java.tag()

    def __truediv__(self, other):
        if isinstance(other, str):
            return Node(self, other)
        if isinstance(other, Node):
            return Node(self, str(other))
        if other is None:
            return Node(self, None)
        return NotImplemented

    def __contains__(self, node):
        if isinstance(node, (str, Node)):
            if (self/node).exists():
                return True
        return False

    def __iter__(self):
        yield from (self/None).children()

    ####################################
    # Inspection                       #
    ####################################

    def name(self):
        """Returns the model's name."""
        name = str(self.java.label())
        if name.endswith('.mph'):
            name = name.rsplit('.', maxsplit=1)[0]
        return name

    def file(self):
        """Returns the absolute path to the file the model was loaded from."""
        return Path(str(self.java.getFilePath())).resolve()

    def version(self):
        """Returns the Comsol version the model was last saved with."""
        version = str(self.java.getComsolVersion())
        return match(r'(?i)Comsol.+?(\d[0-9.a-z]*)', version).group(1)

    def functions(self):
        """Returns the names of all globally defined functions."""
        return [child.name() for child in self/'functions']

    def components(self):
        """Returns the names of all model components."""
        return [child.name() for child in self/'components']

    def geometries(self):
        """Returns the names of all geometry sequences."""
        return [child.name() for child in self/'geometries']

    def selections(self):
        """Returns the names of all selections."""
        return [child.name() for child in self/'selections']

    def physics(self):
        """Returns the names of all physics interfaces."""
        return [child.name() for child in self/'physics']

    def multiphysics(self):
        """Returns the names of all multiphysics interfaces."""
        return [child.name() for child in self/'multiphysics']

    def materials(self):
        """Returns the names of all materials."""
        return [child.name() for child in self/'materials']

    def meshes(self):
        """Returns the names of all mesh sequences."""
        return [child.name() for child in self/'meshes']

    def studies(self):
        """Returns the names of all studies."""
        return [child.name() for child in self/'studies']

    def solutions(self):
        """Returns the names of all solutions."""
        return [child.name() for child in self/'solutions']

    def datasets(self):
        """Returns the names of all datasets."""
        return [child.name() for child in self/'datasets']

    def plots(self):
        """Returns the names of all plots."""
        return [child.name() for child in self/'plots']

    def exports(self):
        """Returns the names of all exports."""
        return [child.name() for child in self/'exports']

    def modules(self):
        """Returns the names of modules/products required to be licensed."""
        return [modules.get(key, key) for key in self.java.getUsedProducts()]

    ####################################
    # Solving                          #
    ####################################

    def build(self, geometry=None):
        """Builds the named geometry, or all of them if none given."""
        geometries = self/'geometries'
        if geometry is None:
            if not geometries.children():
                error = 'No geometry sequence defined in the model.'
                log.error(error)
                raise RuntimeError(error)
        elif isinstance(geometry, str):
            geometry = geometries/geometry
        elif isinstance(geometry, Node):
            if not geometry.parent() == self/'geometries':
                error = f'Node "{geometry}" is not a geometry node.'
                log.error(error)
                raise ValueError(error)
        else:
            error = f'Geometry {geometry!r} is neither string nor node.'
            log.error(error)
            raise TypeError(error)
        if geometry and not geometry.exists():
            error = f'Geometry sequence "{geometry.name()}" does not exist.'
            log.error(error)
            raise LookupError(error)
        nodes = [geometry] if geometry else geometries.children()
        for node in nodes:
            log.info(f'Running geometry sequence "{node.name()}".')
            node.run()
            log.info('Finished geometry sequence.')

    def mesh(self, mesh=None):
        """Runs the named mesh sequence, or all of them if none given."""
        meshes = self/'meshes'
        if mesh is None:
            if not meshes.children():
                error = 'No mesh sequences defined in the model.'
                log.error(error)
                raise RuntimeError(error)
        elif isinstance(mesh, str):
            mesh = meshes/mesh
        elif isinstance(mesh, Node):
            if not mesh.parent() == self/'meshes':
                error = f'Node "{mesh}" is not a mesh node.'
                log.error(error)
                raise ValueError(error)
        else:
            error = f'Mesh {mesh!r} is neither string nor node.'
            log.error(error)
            raise TypeError(error)
        if mesh and not mesh.exists():
            error = f'Mesh sequence "{mesh.name()}" does not exist.'
            log.error(error)
            raise LookupError(error)
        nodes = [mesh] if mesh else meshes.children()
        for node in nodes:
            log.info(f'Running mesh sequence "{node.name()}".')
            node.run()
            log.info('Finished mesh sequence.')

    def solve(self, study=None):
        """Solves the named study, or all of them if none given."""
        studies = self/'studies'
        if study is None:
            if not studies.children():
                error = 'No studies defined in the model.'
                log.error(error)
                raise RuntimeError(error)
        elif isinstance(study, str):
            study = studies/study
        elif isinstance(study, Node):
            if not study.parent() == self/'studies':
                error = f'Node "{study}" is not a study node.'
                log.error(error)
                raise ValueError(error)
        else:
            error = f'Study {study!r} is neither string nor node.'
            log.error(error)
            raise TypeError(error)
        if study and not study.exists():
            error = f'Study "{study.name()}" does not exist.'
            log.error(error)
            raise LookupError(error)
        nodes = [study] if study else studies.children()
        for node in nodes:
            log.info(f'Running study "{node.name()}".')
            node.run()
            log.info('Finished solving study.')

    ####################################
    # Evaluation                       #
    ####################################

    def inner(self, dataset=None):
        """
        Returns the indices and values of inner solutions.

        These are the solution indices and time values in
        time-dependent studies, returned as a tuple of an integer
        array and a floating-point array. A `dataset` name may be
        specified. Otherwise the default dataset is used.
        """
        # Validate dataset argument.
        if dataset is not None:
            if isinstance(dataset, str):
                if '/' in dataset:
                    dataset = self/dataset
                else:
                    dataset = self/'datasets'/dataset
            if not isinstance(dataset, Node):
                error = 'Dataset must be a dataset name or dataset node.'
                log.error(error)
                raise TypeError(error)
        if not dataset.exists():
            error = f'Dataset "{dataset.name()}" does not exist.'
            log.error(error)
            raise ValueError(error)

        # Find corresponding solution.
        if 'solution' in dataset.properties():
            tag = dataset.property('solution')
        elif 'data' in dataset.properties():
            tag = dataset.property('data')
        for solution in self/'solutions':
            if solution.tag() == tag:
                break
        else:
            error = f'Dataset "{dataset.name()}" does not refer to a solution.'
            log.error(error)
            raise RuntimeError(error)

        # Get indices from solution info and values from solution itself.
        java    = solution.java
        info    = java.getSolutioninfo()
        indices = array(info.getSolnum(1, True))
        values  = array(java.getPVals())
        return (indices, values)

    def outer(self, dataset=None):
        """
        Returns the indices and values of outer solutions.

        These are the solution indices and values in parametric sweeps,
        returned as a tuple of an integer array and a floating-point
        array. A `dataset` name may be specified. Otherwise the default
        dataset is used.
        """
        # Validate dataset argument.
        if dataset is not None:
            if isinstance(dataset, str):
                if '/' in dataset:
                    dataset = self/dataset
                else:
                    dataset = self/'datasets'/dataset
            if not isinstance(dataset, Node):
                error = 'Dataset must be a dataset name or dataset node.'
                log.error(error)
                raise TypeError(error)
        if not dataset.exists():
            error = f'Dataset "{dataset.name()}" does not exist.'
            log.error(error)
            raise ValueError(error)

        # Find corresponding solution.
        if 'solution' in dataset.properties():
            tag = dataset.property('solution')
        elif 'data' in dataset.properties():
            tag = dataset.property('data')
        for solution in self/'solutions':
            if solution.tag() == tag:
                break
        else:
            error = f'Dataset "{dataset.name()}" does not refer to a solution.'
            log.error(error)
            raise RuntimeError(error)

        # Get indices and values from solution info.
        info = solution.java.getSolutioninfo()
        indices = array(info.getOuterSolnum())
        values = array([info.getPvals([[index,1]])[0][0] for index in indices])
        return (indices, values)

    def evaluate(self, expression, unit=None, dataset=None,
                       inner=None, outer=None):
        """
        Evaluates an expression and returns the numerical results.

        The `expression` may be a string, denoting a single expression,
        or a sequence of strings, denoting multiple. The optional
        `unit` must be given correspondingly. If omitted, default
        units are used. The expression may be a global one, or a scalar
        field, or particle data. Results are returned as (lists of)
        NumPy arrays, of whichever dimensionality they may then have.

        A `dataset` may be specified. Otherwise the expression will
        be evaluated on the default dataset. If the solution stored in
        the dataset is time-dependent, one or several `inner` solutions
        can be preselected, either by an index number, a sequence of
        indices, or by passing `'first`'/`'last'` to select the very
        first/last index. If the dataset represents a parameter sweep,
        the `outer` solution(s) can be selected by index or sequence
        of indices.

        Please note that this method, while broad in its intended scope,
        covers common use cases, but not all of them. In case it fails
        to return the expected results, consider using the Comsol API
        features directly via the `.java` attribute of this class, and
        refer to the "Results" chapter in the Comsol Programming Manual
        for guidance.
        """
        # Validate input arguments.
        if dataset is not None:
            if isinstance(dataset, str):
                if '/' in dataset:
                    dataset = self/dataset
                else:
                    dataset = self/'datasets'/dataset
            if not isinstance(dataset, Node):
                error = 'Dataset must be a dataset name or dataset node.'
                log.error(error)
                raise TypeError(error)
        if not (inner is None
                or (isinstance(inner, str) and inner in ('first', 'last'))
                or (isinstance(inner, list)
                    and all(isinstance(index, int) for index in inner))
                or (isinstance(inner, ndarray) and inner.dtype.kind == 'i')):
            error = ('Argument "inner", if specified, must be either '
                     '"first", "last", or a list/array of integers.')
            log.error(error)
            raise TypeError(error)
        if outer is not None and not isinstance(outer, (int, integer)):
            error = 'Argument "outer", if specified, must be an integer index.'
            log.error(error)
            raise TypeError(error)

        # Find the default dataset if nothing specified.
        if not dataset:
            eval = (self/'evaluations').create('Eval')
            tag  = eval.property('data')
            eval.remove()
            for dataset in self/'datasets':
                if dataset.tag() == tag:
                    break
            else:
                error = 'Could not determine default dataset.'
                log.error(error)
                raise RuntimeError(error)

        if not dataset.exists():
            error = f'Dataset "{dataset.name()}" does not exist.'
            log.error(error)
            raise ValueError(error)
        log.info(f'Evaluating "{expression}" '
                    f'on dataset "{dataset.name()}".')

        # Find corresponding solution.
        if 'solution' in dataset.properties():
            tag = dataset.property('solution')
        elif 'data' in dataset.properties():
            tag = dataset.property('data')
        for solution in self/'solutions':
            if solution.tag() == tag:
                break
        else:
            error = f'Dataset "{dataset.name()}" does not refer to a solution.'
            log.error(error)
            raise RuntimeError(error)

        # Make sure solution has actually been computed.
        if solution.java.isEmpty():
            error = 'The solution has not been computed.'
            log.error(error)
            raise RuntimeError(error)

        # Try to perform a global evaluation, which may fail.
        eval = (self/'evaluations').create('Global')
        eval.property('expr', expression)
        if unit:
            eval.property('unit', unit)
        eval.property('data', dataset)
        if outer is not None:
            eval.property('outersolnum', outer)
        try:
            log.debug('Trying global evaluation.')
            java = eval.java
            results = array(java.getData())
            if java.isComplex():
                results = results.astype('complex')
                results += 1j * array(java.getImagData())
            eval.remove()
            log.info('Finished global evaluation.')
            if inner is None:
                pass
            elif inner == 'first':
                results = results[:, 0, :]
            elif inner == 'last':
                results = results[:, -1, :]
            else:
                if isinstance(inner, list):
                    inner = array(inner)
                results = results[:, inner-1, :]
            return results.squeeze()
        # Move on if this fails. Seems to not be a global expression then.
        except Exception:
            log.debug('Global evaluation failed. Moving on.')

        # For particle datasets, create an "EvalPoint" feature.
        if dataset.type() == 'Particle':
            eval = (self/'evaluations').create('EvalPoint')
            if inner in ('first', 'last'):
                eval.property('innerinput', inner)
            elif inner is not None:
                eval.property('innerinput', 'manual')
                eval.property('solnum', inner)
        # Otherwise create an "Eval" feature.
        else:
            eval = (self/'evaluations').create('Eval')

        # Set up the evaluation feature.
        eval.property('expr', expression)
        if unit:
            eval.property('unit', unit)
        eval.property('data', dataset)
        if outer is not None:
            eval.property('outersolnum', outer)

        # Retrieve the data.
        log.info('Retrieving data.')
        java = eval.java
        if dataset.type() == 'Particle':
            results = array(java.getReal())
            if java.isComplex():
                results = results.astype('complex')
                results += 1j * array(java.getImag())
            if isinstance(expression, (tuple, list)):
                shape = results.shape[1:]
                results = results.reshape(len(expression), -1, *shape)
        else:
            results = array(java.getData())
            if java.isComplex():
                results = results.astype('complex')
                results += 1j * array(java.getImagData())
            if inner == 'first':
                results = results[:, 0, :]
            elif inner == 'last':
                results = results[:, -1, :]
            elif inner is not None:
                if isinstance(inner, list):
                    inner = array(inner)
                results = results[:, inner-1, :]
        log.info('Finished retrieving data.')

        # Remove the temporary evaluation feature we added to the model.
        eval.remove()

        # Squeeze out singleton array dimensions.
        if isinstance(expression, (list, tuple)):
            results = [result.squeeze() for result in results]
        else:
            results = results.squeeze()

        # Return array of results.
        return results

    ####################################
    # Interaction                      #
    ####################################

    def rename(self, name):
        """Assigns a new name to the model."""
        self.java.label(name)

    def parameter(self, name, value=None, unit=None, description=None,
                        evaluate=False):
        """
        Returns or sets the parameter of the given name.

        Returns the value of parameter `name` if no `value` is given.
        Otherwise sets the value.

        Values are accepted as expressions (strings, possibly including
        the unit inside square brackets) or as numerical values
        (referring to default units).

        By default, values are returned as strings, i.e. the expression
        as entered in the user interface. That expression may include
        the unit, again inside brackets. If the option `evaluate` is set
        to `True`, the numerical value that the expression evaluates to
        is returned.

        *Warning*: The optional arguments `unit` and `description` are
        deprecated and will be removed in a future release. Include the
        unit in the value expression and call the `description()` method
        to change a parameter description.
        """
        if unit is not None:
            warn('Argument "unit" to Model.parameter() is deprecated. '
                 'Include the unit in the value inside square brackets.')
            if value:
                value = f'{value} [{unit}]'
        if description is not None:
            warn('Argument "description" to Model.parameter() is deprecated. '
                 'Call .description() instead.')
            self.description(name, description)
        if value is None:
            if not evaluate:
                try:
                    return str(self.java.param().get(name))
                except Exception:
                    error = f'Parameter "{name}" is not defined.'
                    log.error(error)
                    raise ValueError(error) from None
            else:
                try:
                    return self.java.param().evaluate(name)
                except Exception:
                    try:
                        value = self.java.param().evaluateComplex(name)
                        return complex(value[0], value[1])
                    except Exception:
                        error = f'Evaluation of parameter "{name}" failed.'
                        log.error(error)
                        raise RuntimeError(error) from None
        else:
            if isinstance(value, complex):
                value = str(value)
            self.java.param().set(name, value)

    def parameters(self, evaluate=False):
        """
        Returns the global model parameters.

        The parameters are returned as a dictionary indexed by the
        parameter names and mapping to the parameter values.

        Value are returned as string expressions, i.e. as entered by
        the user, unless `evaluate` is set to `True`, in which case
        the expressions are evaluated and the corresponding numbers
        are returned.

        *Warning*: Prior to version 1.0, this method would return
        a list of named tuples holding name, value, and description.
        It now returns a dictionary, which is a breaking change that
        may require application code to be adapted. The descriptions
        can be retrieved by additionally calling `.description()` or
        `.descriptions()`.
        """
        if not evaluate:
            return {str(name): str(self.java.param().get(name))
                    for name in self.java.param().varnames()}
        else:
            return {str(name): self.java.param().evaluate(name)
                    for name in self.java.param().varnames()}

    def description(self, name, text=None):
        """
        Returns or sets the description of the named parameter.

        If no `text` is given, returns the text description of
        parameter `name`. Otherwise sets it.
        """
        if text is not None:
            value = self.parameter(name)
            self.java.param().set(name, value, text)
        else:
            return str(self.java.param().descr(name))

    def descriptions(self):
        """Returns all parameter descriptions as a dictionary."""
        return {name: self.description(name) for name in self.parameters()}

    def property(self, node, name, value=None):
        """
        Returns or changes the value of the named node property.

        If no `value` is given, returns the value of property `name`.
        Otherwise sets the property to the given value.
        """
        return (self/node).property(name, value)

    def properties(self, node):
        """Returns names and values of all node properties as a dictionary."""
        return (self/node).properties()

    def create(self, node, *arguments):
        """
        Creates a new child node.

        If the given `node` does not exist, creates a node with its
        name in the node's parent group. Otherwise creates a child
        node underneath the given node and assigns it an automatically
        generated unique name/label.

        Refer to the Comsol documentation for the values of valid
        arguments. It is often just the feature type of the child node
        to be created, given as a string such as "Block", but may also
        require different or more arguments.

        Returns the newly created child node as a `Node` instance.
        """
        node = self/node
        if node.exists():
            return node.create(*arguments)
        else:
            return node.parent().create(*arguments, name=node.name())

    def remove(self, node):
        """Removes the node from the model tree."""
        (self/node).remove()

    ####################################
    # Files                            #
    ####################################

    def import_(self, node, file):
        """
        Imports external data from a file and assigns it to the node.

        Note the trailing underscore in the method name. It is needed
        so that the Python parser does not treat the name as an
        `import` statement.
        """
        if isinstance(node, str):
            node = self/node
        if not node.exists():
            error = f'Node "{node}" does not exist in model tree.'
            log.error(error)
            raise LookupError(error)
        node.import_(file)

    def export(self, node=None, file=None):
        """
        Runs the export node, either given by name or node reference.

        A `file` name can be specified. Otherwise the file name defined
        in the node's properties will be used. If called without any
        arguments, all export nodes defined in the model are run using
        the default file names.

        Note that some export nodes, namely animations, require a
        property other than `filename` to be set, and therefore passing
        a `file` argument will fail. This may be corrected in a future
        release. See [issue #43].

        [issue #43]: https://github.com/MPh-py/MPh/issues/43
        """
        if node is None:
            for node in self/'exports':
                log.info(f'Running export node "{node.name()}".')
                node.run()
                log.info('Finished running export.')
        else:
            if isinstance(node, str):
                if '/' in node:
                    node = self/node
                else:
                    node = self/'exports'/node
            if not node.exists():
                error = f'Node "{node}" does not exist in model tree.'
                log.error(error)
                raise ValueError(error)
            if file:
                node.property('filename', str(file))
            log.info(f'Running export node "{node.name()}".')
            node.run()
            log.info('Finished running export.')

    def clear(self):
        """Clears stored solution, mesh, and plot data."""
        log.info('Clearing stored plot data.')
        (self/'plots').java.clearStoredPlotData()
        log.info('Finished clearing plots.')
        log.info('Clearing solution data.')
        for solution in self/'solutions':
            solution.java.clearSolution()
        log.info('Finished clearing solutions.')
        log.info('Clearing mesh data.')
        for mesh in self/'meshes':
            mesh.java.clearMesh()
        log.info('Finished clearing meshes.')

    def reset(self):
        """Resets the modeling history."""
        log.info('Resetting modeling history.')
        self.java.resetHist()
        log.info('Finished resetting history.')

    def save(self, path=None, format=None):
        """
        Saves the model at the given file-system path.

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

        # Coerce paths given as string to Path objects.
        if path:
            path = Path(path)

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
                log.error(error)
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
            log.error(error)
            raise ValueError(error)

        # Use model name if no file name specified.
        if path is None:
            file = self.file()
            if format == 'Comsol':
                if file.is_file():
                    log.info(f'Saving model "{self}".')
                    self.java.save()
                elif file.is_dir():
                    file = file/f'{self}.{type}'
                    log.info(f'Saving model as "{file.name}".')
                    self.java.save(str(file))
            else:
                if file.is_file():
                    file = file.with_suffix(f'.{type}')
                elif file.is_dir():
                    file = file/f'{self}.{type}'
                log.info(f'Saving model as "{file.name}".')
                self.java.save(str(file), type)
        # Otherwise save at given path.
        else:
            if path.is_dir():
                file = (path/self.name()).with_suffix(f'.{type}')
            else:
                file = path.with_suffix(f'.{type}')
            log.info(f'Saving model as "{file.name}".')
            if format == 'Comsol':
                self.java.save(str(file))
            else:
                self.java.save(str(file), type)
        log.info('Finished saving model.')

    ####################################
    # Deprecation                      #
    ####################################

    def features(self, physics):
        # Returns the names of all features in a given physics interface.
        #
        # The term feature refers to the nodes defined under a physics
        # interface. They define the differential equations, boundary
        # conditions, initial values, etc.
        warn('Model.features() is deprecated. Use the Node class instead.')
        if physics not in self.physics():
            error = f'No physics interface named "{physics}".'
            log.error(error)
            raise LookupError(error)
        tags = [tag for tag in self.java.physics().tags()]
        ptag = tags[self.physics().index(physics)]
        tags = [tag for tag in self.java.physics(ptag).feature().tags()]
        return [str(self.java.physics(ptag).feature(ftag).label())
                for ftag in tags]

    def toggle(self, physics, feature, action='flip'):
        # Enables or disables features of a physics interface.
        #
        # If `action` is `'flip'` (the default), it enables the feature
        # if it is currently disabled or disables it if enabled. Pass
        # `'enable'` or `'on'` to enable the feature regardless of its
        # current state. Pass `'disable'` or `'off'` to disable it.
        warn('Model.toggle() is deprecated. Use the Node class instead.')
        if physics not in self.physics():
            error = f'No physics interface named "{physics}".'
            log.error(error)
            raise LookupError(error)
        tags = [tag for tag in self.java.physics().tags()]
        ptag = tags[self.physics().index(physics)]
        node = self.java.physics(ptag)
        if feature not in self.features(physics):
            error = f'No feature named "{feature}" in physics "{physics}".'
            log.error(error)
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

    def load(self, file, interpolation):
        # Loads data from a file and assigns it to an interpolation function.
        warn('Model.load() is deprecated. Call .import_() instead.')
        for tag in self.java.func().tags():
            if str(self.java.func(tag).label()) == interpolation:
                break
        else:
            error = f'Interpolation function "{interpolation}" does not exist.'
            log.error(error)
            raise LookupError(error)
        file = Path(file)
        log.info(f'Loading external data from file "{file.name}".')
        self.java.func(tag).discardData()
        self.java.func(tag).set('filename', f'{file}')
        self.java.func(tag).importData()
        log.info('Finished loading external data.')
