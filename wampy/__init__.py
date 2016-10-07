# Set default logging handler to avoid "No handler found" warnings.
import logging

import eventlet

from wampy.bases import Peer  # NOQA
from wampy.peers import Client  # NOQA


try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

root = logging.getLogger(__name__)
root.addHandler(NullHandler())


eventlet.monkey_patch()
root.warning('eventlet has monkey patched your environment')
