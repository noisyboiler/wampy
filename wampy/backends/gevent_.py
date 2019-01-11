# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import gevent
import gevent.queue
import gevent.monkey

from wampy.errors import WampyTimeOutError
from wampy.interfaces import Async


class Gevent(Async):

    def __init__(self):
        self.message_queue = gevent.queue.Queue()

    def queue(self):
        return gevent.queue.Queue()

    def Timeout(self, timeout, raise_after=True):
        return gevent.Timeout(timeout, raise_after)

    @property
    def QueueEmpty(self):
        return gevent.queue.Empty

    def receive_message(self, timeout):
        try:
            message = self._wait_for_message(timeout)
        except gevent.Timeout:
            raise WampyTimeOutError(
                "no message returned (timed-out in {})".format(timeout)
            )
        return message

    def spawn(self, *args, **kwargs):
        gthread = gevent.spawn(*args, **kwargs)
        return gthread

    def sleep(self, time=0):
        gevent.sleep(time)

    def _wait_for_message(self, timeout):
        q = self.message_queue

        with gevent.Timeout(timeout):
            while q.qsize() == 0:
                gevent.sleep()

        message = q.get()
        return message
