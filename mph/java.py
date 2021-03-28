"""Facilitates access to the Java layer."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import jpype.types as jtypes           # Java types
import numpy                           # fast numerics


########################################
# Properties                           #
########################################

def property(node, name, value=None):
    """
    Sets or gets the value of the named property defined on a model node.

    If no `value` is given, returns the property `name` defined on the
    model `node` (a Java object) after converting it to the appropriate
    Python data type. Otherwise changes the property after casting the
    received value to the appropriate Java data type.
    """

    if value is None:
        dtype = node.getValueType(name)
        if dtype == 'Int':
            value = int(node.getInt(name))
        elif dtype == 'IntArray':
            value = numpy.array(node.getIntArray(name))
        elif dtype == 'IntMatrix':
            value = numpy.array([line for line in node.getIntMatrix(name)])
        elif dtype == 'Boolean':
            value = node.getBoolean(name)
        elif dtype == 'BooleanArray':
            value = numpy.array(node.getBooleanArray(name))
        elif dtype == 'BooleanMatrix':
            value = numpy.array([line for line in node.getBooleanMatrix(name)])
        elif dtype == 'Double':
            value = node.getDouble(name)
        elif dtype == 'DoubleArray':
            value = numpy.array(node.getDoubleArray(name))
        elif dtype == 'DoubleMatrix':
            value = numpy.array([line for line in node.getDoubleMatrix(name)])
        elif dtype == 'String':
            value = str(node.getString(name))
        elif dtype == 'StringArray':
            value = [str(string) for string in node.getStringArray(name)]
        elif dtype == 'StringMatrix':
            value = [[str(string) for string in line]
                     for line in node.getStringMatrix(name)]
        else:
            raise TypeError(f'Cannot convert Java data type "{dtype}".')
        return value

    else:
        if isinstance(value, numpy.ndarray):
            dtype = str(value.dtype)
            if value.ndim == 1:
                if 'int' in dtype:
                    value = jtypes.JArray(jtypes.JInt)(value)
                elif 'float' in dtype:
                    value = jtypes.JArray(jtypes.JDouble)(value)
                elif 'bool' in dtype:
                    value = jtypes.JArray(jtypes.JBoolean)(value)
                elif 'object' in dtype or dtype.startswith('<U'):
                    value = jtypes.JArray(jtypes.JString)(value)
                else:
                    raise TypeError(f'Cannot convert 1d NumPy arrays of '
                                    f'data type "{dtype}".')
            elif value.ndim == 2:
                if 'int' in dtype or 'float' in dtype or 'bool' in dtype:
                    value = jtypes.JArray.of(value)
                elif 'object' in dtype or dtype.startswith('<U'):
                    java_value = jtypes.JString[value.shape]
                    for i, row in enumerate(value):
                        for j, col in enumerate(row):
                            java_value[i][j] = col
                    value = java_value
                else:
                    raise TypeError(f'Cannot convert 2d NumPy arrays of data '
                                    f'type "{dtype}".')
            else:
                raise TypeError('Cannot convert NumPy arrays of dimension '
                                'higher than 2.')
        elif isinstance(value, int):
            value = jtypes.JInt(value)
        elif isinstance(value, float):
            value = jtypes.JDouble(value)
        elif isinstance(value, bool):
            value = jtypes.JBoolean(value)
        elif isinstance(value, str):
            value = jtypes.JString(value)
        elif isinstance(value, (list, tuple)):
            pass
        else:
            raise TypeError(f'Cannot convert values of Python data type '
                            f'"{type(value).__name__}".')
        node.set(name, value)


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
