from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES


class Router(object):
    """Base class for any Router implementation"""

    def __init__(
            self, host=DEFAULT_HOST, port=DEFAULT_PORT,
    ):
        self.host = host
        self.port = port


class Crossbar(Router):

    def __init__(
            self, host=DEFAULT_HOST, port=DEFAULT_PORT,
            realms=None, roles=None
    ):
        super(Crossbar, self).__init__(host, port)

        self.realms = realms or [DEFAULT_REALM]
        self.roles = roles or DEFAULT_ROLES
