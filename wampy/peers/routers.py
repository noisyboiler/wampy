from .. logger import get_logger

from . bases import RouterBase


class Router(RouterBase):
    """ Represents the "router" side of a WAMP Session.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.logger = get_logger(
            'wampy.peers.router.{}'.format(self.name.replace(' ', '-'))
        )
        self.logger.info('New router: "%s"', self.name)
