"""Process exiting via `sys.exit()` after starting the client."""

import parent # noqa F401
import mph
import sys

mph.start()
sys.exit(2)
