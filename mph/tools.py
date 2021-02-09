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
from numpy import array                # numerical arrays


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
            dtype = str(java.getValueType(name))
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
                value = [str(string) for string in java.getStringArray(name)]
            elif dtype == 'StringMatrix':
                value = [[str(string) for string in line]
                         for line in java.getStringMatrix(name)]
            else:
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
