# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.config.defaults import async_name
from wampy.constants import EVENTLET, GEVENT
from wampy.errors import WampyError


def get_async_adapter():
    if async_name == GEVENT:
        from . gevent_ import Gevent
        _adapter = Gevent()
        return _adapter

    if async_name == EVENTLET:
        from . eventlet_ import Eventlet
        _adapter = Eventlet()
        return _adapter

    raise WampyError(
        'only gevent and eventlet are supported, sorry. help out??'
    )


async_adapter = get_async_adapter()
