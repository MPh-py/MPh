# jpype typecast tester for arrays
import logging
import numpy as np
import jpype
import jpype.types as jtypes
import mph

logger = logging.getLogger(__name__)

# Discover Comsol back-end.
backend = mph.discovery.backend('5.5')

# Start the Java virtual machine.
jpype.startJVM(str(backend['jvm']),
               classpath=str(backend['root']/'plugins'/'*'),
               convertStrings=False)

# default namespace
import java.lang as jlang

# 0-D
test_int = 1
test_float = 1.
test_bool = True
test_string = 'valid'

# 1-D
test_int_array = np.ones((10,), dtype=int)
test_float_array = np.ones((10,), dtype=float)
test_bool_array = np.ones((10,), dtype=bool)
test_string_array = np.array([
    f'string_{i}' for i in range(10)])
test_string_object_array = test_string_array.astype(object)

# 2-D
test_int_matrix = np.ones((10, 10), dtype=int)
test_float_matrix = np.ones((10, 10), dtype=float)
test_bool_matrix = np.ones((10, 10), dtype=bool)
test_string_matrix = np.array([
    f'string_{i}' for i in range(100)]).reshape((10, 10))
test_string_object_matrix = test_string_matrix.astype(object)
# Start the tests
passed = True

# typecast 0D
try:
    print(jtypes.JInt(test_int))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JDouble(test_float))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JBoolean(test_bool))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JString(test_string))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False

#typecast 1D
try:
    print(jtypes.JArray(jtypes.JInt)(test_int_array))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray(jtypes.JDouble)(test_float_array))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray(jtypes.JBoolean)(test_bool_array))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray(jtypes.JString)(test_string_array))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray(jtypes.JString)(test_string_object_array))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False

#typecast 2D
try:
    print(jtypes.JArray.of(test_int_matrix))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray.of(test_float_matrix))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray.of(test_bool_matrix))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray.of(test_string_matrix, dtype=jtypes.JByte))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False
try:
    print(jtypes.JArray.of(test_string_object_matrix, dtype=jtypes.JObject))
except Exception as e:
    logger.exception(f'Test failed with: {e}')
    passed = False