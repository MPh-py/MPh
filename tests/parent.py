"""
Adds the parent folder to the module search path.
"""
__license__ = 'MIT'


import sys
from pathlib import Path

folder = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(folder))
