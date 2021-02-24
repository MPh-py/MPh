"""Raises an exception after starting a client."""
import parent
import mph

server = mph.Server()
client = mph.Client(port=server.port)
raise RuntimeError
