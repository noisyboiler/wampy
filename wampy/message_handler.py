# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os

from wampy.auth import compute_wcs
from wampy.errors import WampProtocolError
from wampy.messages import Authenticate, MESSAGE_TYPE_MAP

logger = logging.getLogger('wampy.messagehandler')


class MessageHandler(object):
    """ Responsible for processing incoming WAMP messages.

    The ``Session`` object receives Messages on behalf of a
    ``Client`` and passes them into a ``MessageHandler``.

    The ``MessageHandler`` is designed to be extensible and be
    configured so that a wampy client can be used as part of
    larger applications. To do this subclass ``MessageHandler``
    and override the ``handle_`` methods you wish to customise,
    then instantiate your ``Client`` with your ``MessageHandler``
    instance.

    .. warning ::
        When subclassing ``MessageHandler`` avoid raising Exceptions
        since messages are handled in a background "green" thread
        and unless you're very careful, you won't see your error
        and you'll lose your background worker too.

    """

    def handle_message(self, message, client):
        # all WAMP paylods on a websocket frame are JSON
        message = json.loads(message)
        wamp_code = message[0]
        if wamp_code not in MESSAGE_TYPE_MAP:
            raise WampProtocolError(
                'unexpected WAMP code: {}'.format(wamp_code)
            )

        logger.debug(
            "received message: %s (%s)",
            MESSAGE_TYPE_MAP[wamp_code], message
        )

        self.client = client
        self.session = client.session

        message_class = MESSAGE_TYPE_MAP[wamp_code]
        # instantiate our Message obj using the incoming payload - but slicing
        # off the WAMP code, which we already know
        message_obj = message_class(*message[1:])

        handler_name = "handle_{}".format(message_obj.name)
        handler = getattr(self, handler_name)
        handler(message_obj)

    def handle_abort(self, message_obj):
        logger.warning(
            "The Router has Aborted the handshake: %s", message_obj.message)
        self.session._message_queue.put(message_obj)

    def handle_authenticate(self, message_obj):
        self.session._message_queue.put(message_obj)

    def handle_challenge(self, message_obj):
        logger.debug("client has been Challenged")
        if 'WAMPYSECRET' not in os.environ:
            # unable to handle this so delegate to the Client
            self.session._message_queue.put(message_obj)
            return

        secret = os.environ['WAMPYSECRET']
        if message_obj.auth_method == 'ticket':
            logger.debug("proceeding with ticket authentication method")
            message = Authenticate(secret)
        else:
            logger.debug("proceeding with wampcra authentication method")
            challenge_data = message_obj.challenge
            signature = compute_wcs(secret, str(challenge_data))
            message = Authenticate(signature.decode("utf-8"))

        self.session.send_message(message)

    def handle_error(self, message_obj):
        logger.error("received error: %s", message_obj.message)
        self.session._message_queue.put(message_obj)

    def handle_event(self, message_obj):
        session = self.session

        payload_list = message_obj.publish_args
        payload_dict = message_obj.publish_kwargs

        func, topic = session.subscription_map[message_obj.subscription_id]

        payload_dict['meta'] = {}
        payload_dict['meta']['topic'] = topic
        payload_dict['meta']['subscription_id'] = message_obj.subscription_id

        func(*payload_list, **payload_dict)

    def handle_goodbye(self, message_obj):
        self.session._message_queue.put(message_obj)

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

        procedure_name = session.registration_map[message_obj.registration_id]
        procedure = getattr(self.client, procedure_name)

        try:
            result = procedure(*args, **kwargs)
        except Exception as exc:
            logger.exception("error calling: %s", procedure_name)
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
        self.session._message_queue.put(message_obj)

    def handle_welcome(self, message_obj):
        logger.info("client %s has been welcomed", self.client.name)
        self.session.session_id = message_obj.session_id
        self.session._message_queue.put(message_obj)
        self.client.register_roles()

    def process_result(self, message_obj, result, exc=None):
        result_kwargs = {}

        procedure_name = self.session.registration_map[
            message_obj.registration_id]

        if exc is not None:
            from wampy.messages import Error

            error_message = Error(
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
            logger.debug("yielding response: %s", yield_message)
            self.session.send_message(yield_message)
