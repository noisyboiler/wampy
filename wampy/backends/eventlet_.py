# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import eventlet

from wampy.errors import WampProtocolError
from wampy.interfaces import Async


class Eventlet(Async):

    def __init__(self):
        self.message_queue = eventlet.Queue()

    def Timeout(self, timeout):
        return eventlet.Timeout(timeout)

    def receive_message(self, timeout):
        try:
            message = self._wait_for_message(timeout)
        except eventlet.Timeout:
            raise WampProtocolError(
                "no message returned (timed-out in {})".format(timeout)
            )
        return message

    def spawn(self, *args, **kwargs):
        gthread = eventlet.spawn(*args, **kwargs)
        return gthread

    def sleep(self, time):
        return eventlet.sleep(time)

    def _wait_for_message(self, timeout):
        q = self.message_queue

        with eventlet.Timeout(timeout):
            while q.qsize() == 0:
                eventlet.sleep()

        message = q.get()
        return message
