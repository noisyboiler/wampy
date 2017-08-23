import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Transport(object):

    @abc.abstractmethod
    def register_router(self, router):
        pass

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def send(self):
        pass

    @abc.abstractmethod
    def receive(self):
        pass
