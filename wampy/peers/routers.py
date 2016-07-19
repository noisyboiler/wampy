import logging

from .. constants import DEFAULT_REALM, DEFAULT_ROLES


class RouterBase(object):
    """ Represents the "router" side of a WAMP Session.
    """

    def __init__(
            self, name, host, port, realm=DEFAULT_REALM, roles=DEFAULT_ROLES
    ):

        self.name = name
        self.host = host
        self.port = port
        self.realm = realm
        self.roles = roles

        self.logger = logging.getLogger(
            'wampy.peers.router.{}'.format(self.name.replace(' ', '-'))
        )
        self.logger.info('New router: "%s"', self.name)


class WampRouter(RouterBase):
    """ simple representation of the state of an active Router
    for a Client to connect to.

    """
