"""Meta information about the application"""

import importlib.metadata

name = 'MPh'
version = '?'
summary = '?'

try:
    metadata = importlib.metadata.metadata(name)
    version = metadata['Version']
    summary = metadata['Summary']
except importlib.metadata.PackageNotFoundError:              # pragma: no cover
    pass
