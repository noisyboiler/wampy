import logging

from wampy.peer import Peer


logger = logging.getLogger(__name__)


class ServiceBase(Peer):

    def __init__(self, **kwags):
        super(Service, self).__init__(kwargs)

        self.registery = {}

    @rpc
    def describe_session

    @rpc
    def list_peers(self):
        logger.debug('get all Peers in session here')
        return

    @rpc
    def list_callables(self):
        logger.debug('get registerd RPC APIs here')
        return 
