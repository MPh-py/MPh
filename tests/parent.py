"""Adds the parent folder to the module search path."""

import sys
from pathlib import Path

folder = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(folder))
