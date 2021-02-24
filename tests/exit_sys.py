"""Exits the Python session after starting a client."""
import parent
import mph
import sys

server = mph.Server()
client = mph.Client(port=server.port)
sys.exit(2)
