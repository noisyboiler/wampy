# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Transport(object):

    @abc.abstractmethod
    def connect(self):
        """ should return ``self`` as the "connection" object """

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def send(self, message):
        pass

    @abc.abstractmethod
    def receive(self):
        pass


@six.add_metaclass(abc.ABCMeta)
class Async(object):

    @abc.abstractmethod
    def Timeout(self, timeout):
        pass

    @abc.abstractmethod
    def receive_message(self, timeout):
        pass

    @abc.abstractmethod
    def spawn(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def sleep(self, time):
        pass
