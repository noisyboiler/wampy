# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Set default logging handler to avoid "No handler found" warnings.
import logging

import gevent.monkey


try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

from wampy.peers.clients import Client  # noqa


root = logging.getLogger(__name__)
root.addHandler(NullHandler())

root.warning('gevent about to monkey patched your environment')
gevent.monkey.patch_all()
