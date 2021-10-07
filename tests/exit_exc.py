"""Raises an exception right after starting a client."""

import parent # noqa F401
import mph

client = mph.start()
raise RuntimeError
