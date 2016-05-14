import eventlet

from ... messages.call import Call
from ... constants import CALLER
from ... messages import Message
from ... mixins import HandleMessageMixin
from ... roles import Caller
from ... logger import get_logger


logger = get_logger('wampy.testing.clients.callers.standalone')


class StandAloneClient(HandleMessageMixin, Caller):
    def __init__(self, router):
        assert router.started

        self._router = router
        self._results = []

        self.start()

    @property
    def name(self):
        return 'Stand Alone Client'

    @property
    def role(self):
        return CALLER

    @property
    def router(self):
        return self._router

    @property
    def config(self):
        return {}

    def rpc(self, procedure):
        message = Call(procedure=procedure)
        message.construct()
        self.send(message)

        response = self.wait_for_response()
        return response

    def send(self, message):
        self.session.send(message)

    def wait_for_response(self, timeout=5):
        with eventlet.Timeout(timeout):
            while not self._results:
                eventlet.sleep()
        return self._results.pop()
