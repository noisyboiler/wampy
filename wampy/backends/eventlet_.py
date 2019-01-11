# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import eventlet

from wampy.errors import WampyTimeOutError
from wampy.interfaces import Async


class Eventlet(Async):

    def __init__(self):
        self.message_queue = eventlet.queue.Queue()

    def queue(self):
        return eventlet.queue.Queue()

    @property
    def QueueEmpty(self):
        return eventlet.queue.Empty

    def Timeout(self, timeout, raise_after=True):
        return eventlet.Timeout(timeout, raise_after)

    def receive_message(self, timeout):
        try:
            message = self._wait_for_message(timeout)
        except eventlet.Timeout:
            raise WampyTimeOutError(
                "no message returned (timed-out in {})".format(timeout)
            )
        return message

    def spawn(self, *args, **kwargs):
        gthread = eventlet.spawn(*args, **kwargs)
        return gthread

    def sleep(self, time=0):
        eventlet.sleep(time)

    def _wait_for_message(self, timeout):
        q = self.message_queue

        with eventlet.Timeout(timeout):
            while q.qsize() == 0:
                eventlet.sleep()

        message = q.get()
        return message
