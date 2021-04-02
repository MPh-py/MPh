"""Facilitates access to the Java layer."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import jpype.types as jtypes           # Java types
import numpy                           # fast numerics
from pathlib import Path               # file-system paths


########################################
# Properties                           #
########################################
def typecast_to_java(input):
    """
    This function handles the basic typecast when not connected to
    a java object. This is needed in node creation when the object does not
    exists yet.

    Typecasting to python needs a ajva object for a mutlitude of checks,
    thus this can not be externalized easily.
    """
    if isinstance(input, bool):
        value = jtypes.JBoolean(input)
    elif isinstance(input, int):
        value = jtypes.JInt(input)
    elif isinstance(input, float):
        value = jtypes.JDouble(input)
    elif isinstance(input, str):
        value = jtypes.JString(input)
    elif isinstance(input, Path):
        value = jtypes.JString(str(input))
    elif isinstance(input, (list, tuple)):
        value = input
    elif isinstance(input, numpy.ndarray):
        dtype = str(input.dtype)
        if input.ndim == 1:
            if 'int' in dtype:
                value = jtypes.JArray(jtypes.JInt)(input)
            elif 'float' in dtype:
                value = jtypes.JArray(jtypes.JDouble)(input)
            elif 'bool' in dtype:
                value = jtypes.JArray(jtypes.JBoolean)(input)
            elif 'object' in dtype or dtype.startswith('<U'):
                value = jtypes.JArray(jtypes.JString)(input)
            else:
                raise TypeError(f'Cannot convert 1d NumPy arrays of '
                                f'data type "{dtype}".')
        elif input.ndim == 2:
            if 'int' in dtype or 'float' in dtype or 'bool' in dtype:
                value = jtypes.JArray.of(input)
            elif 'object' in dtype or dtype.startswith('<U'):
                java_value = jtypes.JString[input.shape]
                for i, row in enumerate(input):
                    for j, col in enumerate(row):
                        java_value[i][j] = col
                value = java_value
            else:
                raise TypeError(f'Cannot convert 2d NumPy arrays of data '
                                f'type "{dtype}".')
        else:
            raise TypeError('Cannot convert NumPy arrays of dimension '
                            'higher than 2.')
    else:
        raise TypeError(f'Cannot convert values of Python data type '
                        f'"{type(input).__name__}".')
    return value

def typecast_to_python(node, name):
    """
    Reads and typecasts node (specify java object) properties from java
    to python
    """
    dtype = node.getValueType(name)
    if dtype == 'Boolean':
        return node.getBoolean(name)
    elif dtype == 'BooleanArray':
        return numpy.array(node.getBooleanArray(name))
    elif dtype == 'BooleanMatrix':
        return numpy.array([line for line in node.getBooleanMatrix(name)])
    elif dtype == 'Double':
        return node.getDouble(name)
    elif dtype == 'DoubleArray':
        return numpy.array(node.getDoubleArray(name))
    elif dtype == 'DoubleMatrix':
        return numpy.array([line for line in node.getDoubleMatrix(name)])
    elif dtype == 'File':
        return Path(str(node.getString(name)))
    elif dtype == 'Int':
        return int(node.getInt(name))
    elif dtype == 'IntArray':
        return numpy.array(node.getIntArray(name))
    elif dtype == 'IntMatrix':
        return numpy.array([line for line in node.getIntMatrix(name)])
    elif dtype == 'None':
        return None
    elif dtype == 'String':
        return str(node.getString(name))
    elif dtype == 'StringArray':
        return [str(string) for string in node.getStringArray(name)]
    elif dtype == 'StringMatrix':
        return [[str(string) for string in line]
                for line in node.getStringMatrix(name)]
    else:
        raise TypeError(f'Cannot convert Java data type "{dtype}".')


########################################
# Introspection                        #
########################################

def inspect(node):
    """
    Inspects a `node` (Java object) in the model tree.

    This is basically a "pretty-fied" version of the output from the
    built-in `dir` command. It displays (prints to the console) the
    methods of a model node (as given by the Comsol API) as well as
    the node's properties (if any are defined).

    The node's name, tag, and documentation reference marker are
    listed first. These access methods and a few others, which are
    common to all objects, are suppressed in the method list further
    down, for the sake of clarity.
    """

    # Display general information about the feature.
    print(f'name:    {node.name()}')
    print(f'tag:     {node.tag()}')
    try:
        print(f'type:    {node.getType()}')
    except AttributeError:
        pass
    print(f'display: {node.getDisplayString()}')
    print(f'doc:     {node.docMarker()}')

    # Display comments and notify if feature is deactivated or has warnings.
    comments = str(node.comments())
    if comments:
        print(f'comment: {comments}')
    if not node.isActive():
        print('This feature is currently deactivated.')
    try:
        if node.hasWarning():
            print('This feature has warnings.')
    except AttributeError:
        pass

    # Introspect the feature's attributes.
    attributes = [attribute for attribute in dir(node)]

    # Display properties if any are defined.
    if 'properties' in attributes:
        print('properties:')
        names = [str(property) for property in node.properties()]
        for name in names:
            try:
                value = property(node, name)
            except TypeError:
                value = '[?]'
            print(f'  {name}: {value}')

    # Define a list of common methods to be suppressed in the output.
    suppress = ['name', 'label', 'tag', 'getType', 'getDisplayString',
                'docMarker', 'help', 'comments', 'toString', 'icon',
                'properties', 'hasProperty', 'set',
                'getEntryKeys', 'getEntryKeyIndex', 'getValueType',
                'getInt',     'getIntArray',     'getIntMatrix',
                'getBoolean', 'getBooleanArray', 'getBooleanMatrix',
                'getDouble',  'getDoubleArray',  'getDoubleMatrix',
                'getString',  'getStringArray',  'getStringMatrix',
                'version', 'author', 'resetAuthor', 'lastModifiedBy',
                'dateCreated', 'dateModified', 'timeCreated', 'timeModified',
                'active', 'isActive', 'isactive', 'hasWarning',
                'class_', 'getClass', 'hashCode',
                'notify', 'notifyAll', 'wait']

    # Display the feature's methods.
    print('methods:')
    for name in attributes:
        if name.startswith('_') or name in suppress:
            continue
        print(f'  {name}')
