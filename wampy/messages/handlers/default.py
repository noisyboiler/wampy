import logging

from wampy.messages import Message
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages.yield_ import Yield
from wampy.errors import WampError

logger = logging.getLogger('wampy.messagehandler')


class DefaultMessageHandler(object):

    def __init__(self, client, session, message_queue):
        self.client = client
        self.session = session
        self.message_queue = message_queue

    def __call__(self, *args, **kwargs):
        return self.handle_message(*args, **kwargs)

    def handle_message(self, message):
        logger.info(
            "received message: %s", MESSAGE_TYPE_MAP[message[0]]
        )

        wamp_code = message[0]
        if wamp_code == Message.REGISTERED:  # 64
            self.message_queue.put(message)

        elif wamp_code == Message.INVOCATION:  # 68
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
            _, _, response_message = message
            self.message_queue.put(message)

        elif wamp_code == Message.RESULT:  # 50
            self.message_queue.put(message)

        elif wamp_code == Message.WELCOME:  # 2
            _, session_id, _ = message
            self.session_id = session_id
            self.message_queue.put(message)

        elif wamp_code == Message.ERROR:
            _, _, _, _, _, errors = message
            logger.error(errors)
            self.message_queue.put(message)

        elif wamp_code == Message.SUBSCRIBED:
            self.message_queue.put(message)

        elif wamp_code == Message.EVENT:
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
