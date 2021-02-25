"""Exits the Python session right after starting a client."""
__license__ = 'MIT'

import parent
import mph
import sys

client = mph.start()
sys.exit(2)
