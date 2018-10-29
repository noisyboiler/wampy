import datetime

from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.roles.subscriber import subscribe


class DateService(Client):
    """ A service that returns the current date.

    usage ::

        $ wampy run docs.examples.services:DateService --router http://example.com:port

    e.g. ::

        $ crossbar start --config ./wampy/testing/configs/crossbar.config.json
        $ wampy run docs.examples.services:SubscribingService --router http://localhost:8080

    """  # NOQA
    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class SubscribingService(Client):
    """ A service that prints out "foo" topic messages

    usage ::

        $ wampy run docs.examples.services:SubscribingService --router http://example.com:port

    e.g. ::

        $ crossbar start --config ./wampy/testing/configs/crossbar.config.json
        $ wampy run docs.examples.services:SubscribingService --router http://localhost:8080

    """  # NOQA
    @subscribe(topic="foo")
    def foo_handler(self, **kwargs):
        print("foo message received: {}".format(kwargs))


class BinaryNumberService(Client):

    @callee
    def get_binary_number(self, number):
        return bin(number)


class FooService(Client):

    @callee
    def get_foo(self):
        return 'foo'
