import logging

from wampy.messages.invocation import InvocationWithMeta
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages import Goodbye, Error, Registered, Welcome
from wampy.errors import WampyError

from . default import MessageHandler

logger = logging.getLogger(__name__)


class InvokeWithMetaMessageHandler(MessageHandler):

    def __init__(self, client):
        super(InvokeWithMetaMessageHandler, self).__init__(
            client=client, messages_to_handle=[
                InvocationWithMeta, Welcome, Registered, Goodbye, Error]
        )

    def handle_message(self, message, context=None, meta=None):
        wamp_code = message[0]
        if wamp_code not in self.messages:
            raise WampyError(
                "No message handler is configured for: {}".format(
                    MESSAGE_TYPE_MAP[wamp_code])
            )

        logger.info(
            "received message: %s", MESSAGE_TYPE_MAP[wamp_code]
        )

        message_class = self.messages[wamp_code]
        message_obj = message_class(*message)
        message_obj.process(message=message, client=self.client)
