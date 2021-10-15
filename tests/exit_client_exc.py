"""Process exiting with exception after starting the client."""

import parent # noqa F401
import mph

mph.start()
raise RuntimeError
