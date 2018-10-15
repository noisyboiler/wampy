import datetime

import pytest

from wampy.cli.run import run
from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.roles.subscriber import subscribe


class DateService(Client):

    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class SubscribingService(Client):

    @subscribe(topic="foo")
    def foo_handler(self, **kwargs):
        print("foo message received: {}".format(kwargs))


class BinaryNumberService(Client):

    @callee
    def get_binary_number(self, number):
        return bin(number)


class TestAppRunne(object):

    @pytest.fixture
    def config_path(self):
        return './wampy/testing/configs/crossbar.json'

    def test_app_runner(self, router, config_path):
        apps = [
            'test.test_app_runner:DateService',
            'test.test_app_runner:SubscribingService',
            'test.test_app_runner:BinaryNumberService',
        ]


        running = run(apps, config_path=config_path, router=router)
        assert running

        raise
