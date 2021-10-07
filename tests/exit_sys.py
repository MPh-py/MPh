"""Exits the Python session right after starting a client."""

import parent # noqa F401
import mph
import sys

client = mph.start()
sys.exit(2)
