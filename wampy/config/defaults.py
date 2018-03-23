# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import os

from wampy.constants import GEVENT, EVENT_LOOP_BACKENDS
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
