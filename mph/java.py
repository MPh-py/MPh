"""Facilitates access to the Java layer."""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
import jpype.types as jtypes           # Java types
from numpy import array, ndarray       # numerical arrays
from logging import getLogger


########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


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
            value = array(node.getIntArray(name))
        elif dtype == 'IntMatrix':
            value = array([line for line in node.getIntMatrix(name)])
        elif dtype == 'Boolean':
            value = node.getBoolean(name)
        elif dtype == 'BooleanArray':
            value = array(node.getBooleanArray(name))
        elif dtype == 'BooleanMatrix':
            value = array([line for line in node.getBooleanMatrix(name)])
        elif dtype == 'Double':
            value = node.getDouble(name)
        elif dtype == 'DoubleArray':
            value = array(node.getDoubleArray(name))
        elif dtype == 'DoubleMatrix':
            value = array([line for line in node.getDoubleMatrix(name)])
        elif dtype == 'String':
            value = str(node.getString(name))
        elif dtype == 'StringArray':
            value = array(
                [str(string) for string in node.getStringArray(name)])
        elif dtype == 'StringMatrix':
            value = array(
                [[str(string) for string in line]
                for line in node.getStringMatrix(name)])
        else:
            logger.error(f'Cannot typecast property {name} of {node.name()}')
            value = '[?]'

        return value

    else:
        if isinstance(value, ndarray):
            dtype_ident = str(value.dtype)
            if value.ndim == 1:
                if 'int' in dtype_ident:
                    value = jtypes.JArray(jtypes.JInt)(value)
                elif 'float' in dtype_ident:
                    value = jtypes.JArray(jtypes.JDouble)(value)
                elif 'bool' in dtype_ident:
                    value = jtypes.JArray(jtypes.JBoolean)(value)
                elif 'object' in dtype_ident or dtype_ident.startswith('<U'):
                    value = jtypes.JArray(jtypes.JString)(value)
                else:
                    logger.error(f'Invalid array datatype (python) for {name}')
                    value = None

            elif value.ndim == 2:
                if 'int' in dtype_ident or 'float' in dtype_ident or 'bool' in dtype_ident:
                    value = jtypes.JArray.of(value)
                elif 'object' in dtype_ident or dtype_ident.startswith('<U'):
                    java_value = jtypes.JString[value.shape]
                    for i, row in enumerate(value):
                        for j, col in enumerate(row):
                            java_value[i][j] = col
                    value = java_value
                else:
                    logger.error(f'Invalid array datatype (python) for {name}')
                    value = None
            else:
                logger.error(f'Invalid array dimension for typecast (>2) of {name}')
                value = None

        else:
            if isinstance(value, int):
                value = jtypes.JInt(value)
            elif isinstance(value, float):
                value = jtypes.JDouble(value)
            elif isinstance(value, bool):
                value = jtypes.JBoolean(value)
            elif isinstance(value, str):
                value = jtypes.JString(value)
            elif isinstance(value, (list, tuple)):
                # Interestingly, those are working quite well...
                ...
            else:
                logger.error(f'Unrecognized data type for {name}')
                value = None

        if value is not None:
            logger.debug(f'Type conversion sucess - setting property {name}')
            node.set(name, value)

        return None

########################################
# Introspection                        #
########################################

def inspect(node):
    """
    Inspects a `node` (Java object) in the model tree.

    This is basically a "pretty-fied" version of the output from the
    built-in `dir` command. It displays (prints to the console) the
    methods of a model node (as given by the Comsol API) as well as
    the node's "properties" (if any are defined).

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
            value = property(node, name)
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
