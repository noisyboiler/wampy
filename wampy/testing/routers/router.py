from wampy.peer import Peer


class Router(Peer):

    def __init__(self, host, config_path):
        """ A "router" implementation of a "Peer".

        :Parameters:
            host : str
                The host address of the Router, e.g. "localhost"
            config_path : str
                The path to the router configuration file.

        """
        super(Router, self).__init__()

        self.host = host
        self.config_path = config_path
