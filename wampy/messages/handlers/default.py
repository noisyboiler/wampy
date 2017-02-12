import logging

from wampy.messages import Message, MESSAGE_TYPE_MAP
from wampy.messages import (
    Goodbye, Error, Event, Invocation, Registered, Result, Subscribed,
    Welcome, Yield)
from wampy.errors import WampError, WampyError

logger = logging.getLogger('wampy.messagehandler')


class MessageHandler(object):

    def __init__(
        self, client, session, message_queue, messages_to_handle=None,
    ):
        """ Responsible for processing incoming WAMP messages.

        :Parameters:
            client : instance of `wampy.peers.clients.Client`
                The wampy client receiving the messages.

            messages_to_handle : list
                A list of Message classes. Only Messages described in
                this list will be accepted.

        """
        self.client = client
        self.session = session
        self.message_queue = message_queue

        if messages_to_handle is None:
            # the rationale here is as follows:-
            # Welcome: mandatory for Session establishment
            # Goodbye: mandatory because GOODBYE is echoed by the Router
            # Registered: a client is likely to be a Callee
            # Invocation: same as above
            # Yield: and again
            # Result: a client is likely to be a Caller
            # Error: for debugging clients
            # Subscribed: because a client is likely to be a Subscriber
            # Event: sames as above
            self.messages_to_handle = [
                Welcome, Goodbye, Registered, Invocation, Yield, Result,
                Error, Subscribed, Event
            ]
        else:
            for message in messages_to_handle:
                # validation here
                pass

            self.messages_to_handle = messages_to_handle

        self.messages = {}
        self._configure_messages()

    def __call__(self, *args, **kwargs):
        return self.handle_message(*args, **kwargs)

    def _configure_messages(self):
        messages = self.messages
        for message in self.messages_to_handle:
            messages[message.WAMP_CODE] = message

    def handle_message(self, message):
        wamp_code = message[0]
        if wamp_code not in self.messages:
            raise WampyError(
                "No message handler is configured for: {}".format(
                    MESSAGE_TYPE_MAP[wamp_code])
            )

        logger.info(
            "received message: %s", MESSAGE_TYPE_MAP[wamp_code]
        )

        if wamp_code == Message.REGISTERED:  # 64
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            self.message_queue.put(message)

        elif wamp_code == Message.INVOCATION:  # 68
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            args = []
            kwargs = {}

            try:
                # no args, no kwargs
                _, request_id, registration_id, details = message
            except ValueError:
                # args, no kwargs
                try:
                    _, request_id, registration_id, details, args = message
                except ValueError:
                    # args and kwargs
                    _, request_id, registration_id, details, args, kwargs = (
                        message)

            registration_id_procedure_name_map = {
                v: k for k, v in self.session.registration_map.items()
            }

            procedure_name = registration_id_procedure_name_map[
                registration_id]

            entrypoint = getattr(self.client, procedure_name)

            try:
                resp = entrypoint(*args, **kwargs)
            except Exception as exc:
                resp = None
                error = str(exc)
            else:
                error = None

            result_kwargs = {}

            result_kwargs['error'] = error
            result_kwargs['message'] = resp
            result_kwargs['_meta'] = {}
            result_kwargs['_meta']['procedure_name'] = procedure_name
            result_kwargs['_meta']['session_id'] = self.session_id
            result_kwargs['_meta']['client_id'] = self.client.id

            result_args = [resp]

            message = Yield(
                request_id,
                result_args=result_args,
                result_kwargs=result_kwargs,
            )
            logger.info("yielding response: %s", message)
            self.session.send_message(message)

        elif wamp_code == Message.GOODBYE:  # 6
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            self.message_queue.put(message)

        elif wamp_code == Message.RESULT:  # 50
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            self.message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            _, session_id, _ = message
            self.session_id = session_id
            self.message_queue.put(message)

        elif wamp_code == Message.ERROR:
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            _, _, _, _, _, errors = message
            logger.error(errors)
            self.message_queue.put(message)

        elif wamp_code == Message.SUBSCRIBED:
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            self.message_queue.put(message)

        elif wamp_code == Message.EVENT:
            message_class = self.messages[wamp_code]
            message_obj = message_class(*message)
            message_obj.process(message)

            payload_list = []
            payload_dict = {}

            try:
                # [
                #   EVENT,
                #   SUBSCRIBED.Subscription|id,
                #   PUBLISHED.Publication|id,
                #   Details|dict,
                #   PUBLISH.Arguments|list,
                #   PUBLISH.ArgumentKw|dict]
                # ]
                _, subscription_id, _, details, payload_list, payload_dict = (
                    message)
            except ValueError:

                try:
                    # [
                    #   EVENT,
                    #   SUBSCRIBED.Subscription|id,
                    #   PUBLISHED.Publication|id,
                    #   Details|dict,
                    #   PUBLISH.Arguments|list,
                    # ]
                    _, subscription_id, _, details, payload_list = message
                except ValueError:
                    # [
                    #   EVENT,
                    #   SUBSCRIBED.Subscription|id,
                    #   PUBLISHED.Publication|id,
                    #   Details|dict,
                    # ]
                    _, subscription_id, _, details = message

            func_name, topic = self.session.subscription_map[subscription_id]
            try:
                func = getattr(self.client, func_name)
            except AttributeError:
                raise WampError(
                    "Event handler not found: {}".format(func_name)
                )

            payload_dict['_meta'] = {}
            payload_dict['_meta']['topic'] = topic
            payload_dict['_meta']['subscription_id'] = subscription_id

            func(*payload_list, **payload_dict)

        else:
            logger.warning(
                'unhandled message: "%s"', message
            )
