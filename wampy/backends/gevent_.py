# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import gevent
import gevent.queue
import gevent.monkey

from wampy.errors import WampProtocolError
from wampy.interfaces import Async


class Gevent(Async):

    def __init__(self):
        self.message_queue = gevent.queue.Queue()

    def Timeout(self, timeout):
        return gevent.Timeout(timeout)

    def receive_message(self, timeout):
        try:
            message = self.message_queue.get(timeout=timeout)
        except gevent.queue.Empty:
            raise WampProtocolError(
                "no message returned (timed-out in {})".format(timeout)
            )
        return message

    def spawn(self, *args, **kwargs):
        gthread = gevent.spawn(*args, **kwargs)
        return gthread

    def sleep(self, time):
        return gevent.sleep(time)
