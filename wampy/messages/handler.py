import logging

from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages import (
    Goodbye, Error, Event, Invocation, Registered, Result, Subscribed,
    Welcome, Yield)
from wampy.errors import WampyError

logger = logging.getLogger('wampy.messagehandler')


class MessageHandler(object):

    # the minimum messages to perform WAMP RPC and PubSub
    DEFAULT_MESSAGES_TO_HANDLE = [
        Welcome, Goodbye, Registered, Invocation, Yield, Result,
        Error, Subscribed, Event
    ]

    def __init__(self, client, messages_to_handle=None):
        """ Responsible for processing incoming WAMP messages.

        :Parameters:
            messages_to_handle : list
                A list of Message classes. Only Messages described in
                this list will be accepted.

        """
        self.client = client
        self.messages_to_handle = (
            messages_to_handle or self.DEFAULT_MESSAGES_TO_HANDLE
        )

        self.messages = {}
        self._configure_messages()

    def __call__(self, *args, **kwargs):
        return self.handle_message(*args, **kwargs)

    def _configure_messages(self):
        messages = self.messages
        for message in self.messages_to_handle:
            messages[message.WAMP_CODE] = message

    def handle_message(self, message, context=None, meta=None):
        wamp_code = message[0]
        if wamp_code not in self.messages:
            raise WampyError(
                "No message handler is configured for: {}".format(
                    MESSAGE_TYPE_MAP[wamp_code])
            )

        logger.info(
            "received message: %s (%s)",
            MESSAGE_TYPE_MAP[wamp_code], message
        )

        message_class = self.messages[wamp_code]
        message_obj = message_class(*message)
        message_obj.process(client=self.client)
