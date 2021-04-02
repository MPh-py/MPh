"""Raises an exception right after starting a client."""
__license__ = 'MIT'

import parent # noqa F401
import mph

client = mph.start()
raise RuntimeError
