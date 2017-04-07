import logging

from wampy.messages import MESSAGE_TYPE_MAP
from wampy.messages import Invocation
from wampy.errors import WampyError

from . default import MessageHandler

logger = logging.getLogger(__name__)


class InvocationWithMeta(Invocation):

    def process(self, message, client):
        session = client.session

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

        procedure_name = client.registration_map[registration_id]
        entrypoint = getattr(client, procedure_name)

        kwargs['meta'] = {}
        kwargs['meta']['procedure_name'] = procedure_name
        kwargs['meta']['session_id'] = session.id

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
        result_kwargs['meta'] = {}
        result_kwargs['meta']['procedure_name'] = procedure_name
        result_kwargs['meta']['session_id'] = session.id

        result_args = [resp]

        from wampy.messages import Yield
        yield_message = Yield(
            request_id,
            result_args=result_args,
            result_kwargs=result_kwargs,
        )
        logger.info("yielding response: %s", yield_message)
        session.send_message(yield_message)


class InvokeWithMetaMessageHandler(MessageHandler):

    def __init__(self, client):
        super(InvokeWithMetaMessageHandler, self).__init__(
            client=client, messages_to_handle=[InvocationWithMeta]
        )

    def handle_message(self, message, context=None, meta=None):
        wamp_code = message[0]
        if wamp_code not in self.messages:
            raise WampyError(
                "No message handler is configured for: {}".format(
                    MESSAGE_TYPE_MAP[wamp_code])
            )

        logger.debug(
            "received message: %s", MESSAGE_TYPE_MAP[wamp_code]
        )

        message_class = self.messages[wamp_code]
        message_obj = message_class(*message)
        message_obj.process(message=message, client=self.client)
