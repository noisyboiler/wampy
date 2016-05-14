import datetime

from ... constants import CALLEE
from ... entrypoints import rpc
from ... logger import get_logger
from ... messages import Message
from ... messages.yield_ import Yield
from ... roles import Callee
from ... registry import Registry


logger = get_logger('wampy.testing.clients.callees.date_service')


class DateService(Callee):
    """ A service that tells you todays date """

    def __init__(self, router=None):
        self._router = router

    @property
    def name(self):
        return 'Date Service'

    @property
    def role(self):
        return CALLEE

    @property
    def config(self):
        return {}

    @property
    def router(self):
        return self._router

    @rpc
    def get_todays_date(self):
        logger.info('getting todays date')
        return datetime.date.today().isoformat()

    def handle_message(self, message):
        logger.info('%s handling a message: "%s"', self.name, message)

        wamp_code = message[0]

        if wamp_code == Message.REGISTERED:
            _, request_id, registration_id = message
            app, func_name = Registry.request_map[request_id]
            Registry.registration_map[registration_id] = app, func_name

            logger.info(
                '%s registered entrypoint "%s" for "%s"',
                self.name, func_name, app.__name__
            )

        elif wamp_code == Message.INVOCATION:
            logger.info('%s handling invocation', self.name)
            _, request_id, registration_id, details = message

            _, procedure_name = Registry.registration_map[
                registration_id]

            entrypoint = getattr(self, procedure_name)
            resp = entrypoint()
            result_args = [resp]

            message = Yield(request_id, result_args=result_args)
            message.construct()
            self.session.send(message)

        elif wamp_code == Message.GOODBYE:
            logger.info('%s handling goodbye', self.name)
            _, _, response_message = message
            assert response_message == 'wamp.close.normal'

        else:
            logger.exception(
                '%s has an unhandled message: "%s"', self.name, wamp_code
            )
