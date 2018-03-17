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
