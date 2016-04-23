from ... entrypoints import rpc
from ... interfaces import Peer


class CalleeApp(Peer):
    def __init__(self):
        self._running = False

    @property
    def name(self):
        return 'test app'

    @property
    def config(self):
        return {}

    @property
    def role(self):
        return 'CALLEE'

    @property
    def start(self):
        print('test app starting up')
        self._running = True

    @property
    def started(self):
        print('test app starting up')
        return self._running

    @property
    def stop(self):
        print('test app stopping running')
        self._running = False

    @rpc
    def this_is_callable_over_rpc(self):
        pass
