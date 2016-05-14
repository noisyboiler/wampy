import eventlet

from ... messages.call import Call
from ... constants import CALLER
from ... messages import Message
from ... roles import Caller
from ... logger import get_logger


logger = get_logger('wampy.testing.clients.callers.standalone')


class StandAloneClient(Caller):
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

    def handle_message(self, message):
        logger.info('%s handling a message: "%s"', self.name, message)

        wamp_code = message[0]

        if wamp_code == Message.RESULT:
            logger.info('%s handling a RESULT', self.name)
            _, request_id, data, response_list = message
            response = response_list[0]
            self._results.append(response)
