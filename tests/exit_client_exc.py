"""Process exiting with exception after starting the client."""

import mph


mph.start()
raise RuntimeError
