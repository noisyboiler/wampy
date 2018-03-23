# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from wampy.constants import GEVENT


async_name = os.environ.get('WAMPY_ASYNC_NAME', GEVENT)
