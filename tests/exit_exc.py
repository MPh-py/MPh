"""Raises an exception right after starting a client."""
__license__ = 'MIT'

import parent
import mph

client = mph.start()
raise RuntimeError
