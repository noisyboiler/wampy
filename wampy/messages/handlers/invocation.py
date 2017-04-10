import logging

from wampy.messages.invocation import InvocationWithMeta
from wampy.messages import Goodbye, Error, Registered, Welcome

from . default import MessageHandler

logger = logging.getLogger(__name__)


class InvokeWithMetaMessageHandler(MessageHandler):

    def __init__(self, client):
        super(InvokeWithMetaMessageHandler, self).__init__(
            client=client, messages_to_handle=[
                InvocationWithMeta, Welcome, Registered, Goodbye, Error]
        )
