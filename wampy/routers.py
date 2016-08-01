# dot attribute lookup data structures for router configurations.
from . constants import DEFAULT_HOST, DEFAULT_PORT


class Crossbar(object):
    """ A default configuration of Crossbar.io
    """
    name = "Crossbar"
    host = DEFAULT_HOST
    port = DEFAULT_PORT
