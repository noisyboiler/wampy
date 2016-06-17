import eventlet

from .. rpc import RpcProxy
from . bases import ClientBase


class WampClient(ClientBase):

    @property
    def name(self):
        return self._name

    @property
    def realm(self):
        return self._realm

    @property
    def roles(self):
        return self._roles

    @property
    def session(self):
        return self._session

    def start(self):
        # kick off the connection and the listener of it
        self._connect_to_router()
        # then then the session over the connection
        self._say_hello_to_router()

        def wait_for_session():
            with eventlet.Timeout(5):
                while self.session is None:
                    eventlet.sleep(0)

        wait_for_session()
        self._register_entrypoints()
        self.logger.info('%s has started', self.name)

    def stop(self):
        self.managed_thread.kill()
        # TODO: say goodbye
        self._session = None
        self.logger.info('%s has stopped', self.name)


class RpcClient(WampClient):
    def __init__(self, *args, **kwargs):
        super(RpcClient, self).__init__(*args, **kwargs)
        self.rpc = RpcProxy(client=self)
