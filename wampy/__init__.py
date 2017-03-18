# Set default logging handler to avoid "No handler found" warnings.
import logging

import eventlet


try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

from wampy.peers.clients import Client  # noqa


root = logging.getLogger(__name__)
root.addHandler(NullHandler())

root.warning('eventlet about to monkey patched your environment')
eventlet.monkey_patch()
