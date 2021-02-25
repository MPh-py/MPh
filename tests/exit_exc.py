"""Raises an exception after starting a client."""
import parent
import mph

client = mph.start()
raise RuntimeError
