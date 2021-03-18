"""
Tools for software development.

This module provides functionality that a user might find helpful
when extending this very package or when developing applications
of their own. It is strictly a helper module for the user. None
of the other modules in this package depend on it.
"""
__license__ = 'MIT'


########################################
# Dependencies                         #
########################################
from logging import getLogger
from numpy import array, ndarray               # numerical arrays
import jpype.types as jtypes
########################################
# Globals                              #
########################################
logger = getLogger(__package__)        # event logger


def _typecast_property(java, name, value=None):
    """
    Typecasts and, if asked, sets a property of a jave node.

    This function handles the interaction with properties of java nodes. Two
    different modes are avaiable - either not specifying a value which then
    reads a property node and typecast its value to python or when specifying a
    value which then typecasts the value to the best fit java object and
    subsequently setting the property.

    Since datatypes need to be converted to and from java to avoid exceptions
    with loosely typed variables in python, this function tries to find the
    closest fit for each conversion direction and converts the value.
    """
    if value is None:
        dtype = java.getValueType(name)
        if dtype == 'Int':
            value = int(java.getInt(name))
        elif dtype == 'IntArray':
            value = array(java.getIntArray(name))
        elif dtype == 'IntMatrix':
            value = array([line for line in java.getIntMatrix(name)])
        elif dtype == 'Boolean':
            value = java.getBoolean(name)
        elif dtype == 'BooleanArray':
            value = array(java.getBooleanArray(name))
        elif dtype == 'BooleanMatrix':
            value = array([line for line in java.getBooleanMatrix(name)])
        elif dtype == 'Double':
            value = java.getDouble(name)
        elif dtype == 'DoubleArray':
            value = array(java.getDoubleArray(name))
        elif dtype == 'DoubleMatrix':
            value = array([line for line in java.getDoubleMatrix(name)])
        elif dtype == 'String':
            value = str(java.getString(name))
        elif dtype == 'StringArray':
            value = array(
                [str(string) for string in java.getStringArray(name)])
        elif dtype == 'StringMatrix':
            value = array(
                [[str(string) for string in line]
                for line in java.getStringMatrix(name)])
        else:
            logger.error(f'Cannot typecast property {name} of {java.name()}')
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
            else:
                logger.error(f'Unrecognized data type for {name}')
                value is None

        if value is not None:
            logger.debug(f'Type conversion sucess - setting property {name}')
            java.set(name, value)

        return None

########################################
# Introspection                        #
########################################

def inspect(java):
    """
    Inspects a Java object representing a Comsol model feature.

    This is basically a "pretty-fied" version of the output from the
    standard `dir` command. It displays (prints to the console) the
    methods of a model node, given as a `java` object as provided by
    the Comsol API, as well as the node's "property" names and values,
    if any are defined.

    The node's name, tag, and documentation reference marker are
    listed first. These access methods and a few others, which are
    common to all objects, are suppressed in the method list further
    down, for the sake of clarity.
    """
    # Display general information about the feature.
    print(f'name:    {java.name()}')
    print(f'tag:     {java.tag()}')
    try:
        print(f'type:    {java.getType()}')
    except AttributeError:
        pass
    print(f'display: {java.getDisplayString()}')
    print(f'doc:     {java.docMarker()}')

    # Display comments and notify if feature is deactivated or has warnings.
    comments = str(java.comments())
    if comments:
        print(f'comment: {comments}')
    if not java.isActive():
        print('This feature is currently deactivated.')
    try:
        if java.hasWarning():
            print('This feature has warnings.')
    except AttributeError:
        pass

    # Introspect the feature's attributes.
    attributes = [attribute for attribute in dir(java)]

    # Display properties if any are defined.
    if 'properties' in attributes:
        print('properties:')
        names = [str(property) for property in java.properties()]
        for name in names:
            value = _typecast_property(java, name)
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
