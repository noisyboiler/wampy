from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES


class Router(object):

    def __init__(
            self, host=DEFAULT_HOST, port=DEFAULT_PORT,
            realms=[DEFAULT_REALM], roles=DEFAULT_ROLES
    ):
        self.host = host
        self.port = port
        self.reals = realms or []
        self.roles = roles
