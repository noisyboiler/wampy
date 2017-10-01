# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from wampy.errors import WampyError

logger = logging.getLogger(__name__)


class RegisterSubscriptionDecorator(object):

    def __init__(self, **kwargs):
        if "topic" not in kwargs:
            raise WampyError(
                "subscriber missing ``topic`` keyword argument"
            )

        self.topic = kwargs['topic']

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            f(*args, **kwargs)

        wrapped_f.subscriber = True
        wrapped_f.topic = self.topic
        wrapped_f.handler = f
        return wrapped_f


subscribe = RegisterSubscriptionDecorator
