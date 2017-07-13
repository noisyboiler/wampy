# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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

    def __init__(self, messages_to_handle=None):
        """ Responsible for processing incoming WAMP messages.

        The ``Session`` object receieves Messages on behalf of a
        ``Client`` and passes them into a ``MessageHandler``.

        The ``MessageHandler`` is designed to be extensible and be
        configured so that a wampy client can be used as part of
        larger applications. To do this subclass ``MessageHandler``
        and override the ``handle_`` methods you wish to customise,
        then instantiate your ``Client`` with your ``MessageHandler``
        instance.

        :Parameters:
            messages_to_handle : list
                A list of Message classes. Only Messages described in
                this list will be accepted.

        """
        self.messages_to_handle = (
            messages_to_handle or self.DEFAULT_MESSAGES_TO_HANDLE
        )

        self.messages = {}
        self._configure_messages()

    def _configure_messages(self):
        messages = self.messages
        for message in self.messages_to_handle:
            messages[message.WAMP_CODE] = message

    def handle_message(self, message, session):
        wamp_code = message[0]
        if wamp_code not in self.messages:
            raise WampyError(
                "No message handler is configured for: {}".format(
                    MESSAGE_TYPE_MAP[wamp_code])
            )

        self.session = session

        logger.info(
            "received message: %s (%s)",
            MESSAGE_TYPE_MAP[wamp_code], message
        )

        message_class = self.messages[wamp_code]
        message_obj = message_class(*message)

        handler_name = "handle_{}".format(message_obj.name)
        handler = getattr(self, handler_name)
        handler(message_obj)

    def handle_event(self, message_obj):
        session = self.session

        payload_list = message_obj.publish_args
        payload_dict = message_obj.publish_kwargs

        func, topic = session.subscription_map[message_obj.subscription_id]

        payload_dict['meta'] = {}
        payload_dict['meta']['topic'] = topic
        payload_dict['meta']['subscription_id'] = message_obj.subscription_id

        func(*payload_list, **payload_dict)

    def handle_error(self, message_obj):
        self.session._message_queue.put(message_obj.message)

    def handle_subscribed(self, message_obj):
        session = self.session

        original_message, handler = session.request_ids[
            message_obj.request_id]
        topic = original_message.topic

        session.subscription_map[message_obj.subscription_id] = handler, topic

    def handle_invocation(self, message_obj):
        session = self.session

        args = message_obj.call_args
        kwargs = message_obj.call_kwargs

        procedure = session.registration_map[message_obj.registration_id]

        try:
            result = procedure(*args, **kwargs)
        except Exception as exc:
            logger.exception("error calling: %s", procedure.__name__)
            result = None
            error = exc
        else:
            error = None

        self.process_result(message_obj, result, exc=error)

    def handle_registered(self, message_obj):
        session = self.session
        procedure_name = session.request_ids[message_obj.request_id]
        session.registration_map[message_obj.registration_id] = procedure_name

    def handle_result(self, message_obj):
        self.session._message_queue.put(message_obj.message)

    def handle_welcome(self, message_obj):
        self.session.session_id = message_obj.session_id

    def handle_goodbye(self, message_obj):
        pass

    def process_result(self, message_obj, result, exc=None):
        result_kwargs = {}

        procedure = self.session.registration_map[
            message_obj.registration_id]
        procedure_name = procedure.__name__

        if exc is not None:
            from wampy.messages import Error

            error_message = Error(
                wamp_code=Error.WAMP_CODE,
                request_type=68,  # the failing message wamp code
                request_id=message_obj.request_id,
                error=procedure_name,
                kwargs_dict={
                    'exc_type': exc.__class__.__name__,
                    'message': str(exc),
                    'call_args': message_obj.call_args,
                    'call_kwargs': message_obj.call_kwargs,
                },
            )
            logger.info("returning with Error: %s", error_message)
            error_message.serialize()
            self.session.send_message(error_message)

        else:
            from wampy.messages import Yield

            result_kwargs['message'] = result
            result_kwargs['meta'] = {}
            result_kwargs['meta']['procedure_name'] = procedure_name
            result_kwargs['meta']['session_id'] = self.session.id
            result_args = [result]

            yield_message = Yield(
                message_obj.request_id,
                result_args=result_args,
                result_kwargs=result_kwargs,
            )
            logger.info("yielding response: %s", yield_message)
            self.session.send_message(yield_message)
