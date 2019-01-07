# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# a temporary solution to configuration. wampy needs to decide how
# users can configure him, e.g. config.yaml
# for now, env varialbes are the way to override defaults.

import logging
import os

from wampy.constants import (
    DEFAULT_HEARTBEAT_SECONDS, DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
    GEVENT, EVENT_LOOP_BACKENDS
)
from wampy.errors import WampyError

logger = logging.getLogger(__name__)


async_name = os.environ.get('WAMPY_ASYNC_NAME', GEVENT)
logger.info('asycn name is "%s"', async_name)
if async_name not in EVENT_LOOP_BACKENDS:
    logger.error('unsupported event loop for wampy! "%s"', async_name)
    raise WampyError(
        'export your WAMPY_ASYNC_NAME os environ value to be one of "{}" '
        'or just remove and use the default gevent'.format(
            EVENT_LOOP_BACKENDS
        ),
    )

heartbeat = os.environ.get(
    'WEBSOCKET_HEARTBEAT', DEFAULT_HEARTBEAT_SECONDS,
)

heartbeat_timeout = os.environ.get(
    'HEARTBEAT_TIMEOUT_SECONDS', DEFAULT_HEARTBEAT_TIMEOUT_SECONDS,
)
