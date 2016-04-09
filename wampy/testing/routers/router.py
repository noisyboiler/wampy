from wampy.interfaces import Peer


class Router(Peer):

    def __init__(self, host):
        super(Router, self).__init__()
        self.host = host
