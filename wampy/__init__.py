# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

from wampy.config.defaults import async_name
from wampy.constants import EVENTLET, GEVENT

logger = logging.getLogger("wampy")


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s:%(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    root = logging.getLogger()
    root.addHandler(NullHandler())

    logger.info("logging configured")


def configure_async():
    if async_name == GEVENT:
        import gevent.monkey
        gevent.monkey.patch_all()
        logger.warning('gevent monkey-patched your environment')

    if async_name == EVENTLET:
        import eventlet
        eventlet.monkey_patch()
        logger.warning('eventlet monkey-patched your environment')


configure_async()
configure_logging()

logger.info('wampy starting up with event loop: %s', async_name)
