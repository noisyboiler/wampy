# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

import eventlet
import gevent
import gevent.queue
import gevent.monkey

from wampy.constants import EVENTLET, GEVENT
from wampy.errors import WampProtocolError, WampyError
from wampy.interfaces import Async


logger = logging.getLogger(__name__)


def get_async_adapter():

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

    from wampy.config.defaults import async_name
    if async_name == GEVENT:
        _adapter = Gevent()
        return _adapter

    if async_name == EVENTLET:
        _adapter = Eventlet()
        return _adapter

    raise WampyError(
        'only gevent and eventlet are supported, sorry. help out??'
    )


async_adapter = get_async_adapter()
