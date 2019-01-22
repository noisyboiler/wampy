import datetime

import pytest

from wampy.cli.run import run
from wampy.peers.clients import Client


class TestAppRunner(object):

    @pytest.fixture
    def config_path(self):
        return './wampy/testing/configs/crossbar.json'

    def test_app_runner(self, router, config_path):
        apps = [
            'docs.examples.services:DateService',
            'docs.examples.services:BinaryNumberService',
            'docs.examples.services:FooService',
        ]

        runner = run(apps, config_path=config_path, router=router)

        # now check we can call these wonderful services
        client = Client(router=router)
        with client:
            date = client.rpc.get_todays_date()
            binary_number = client.rpc.get_binary_number(46)
            foo = client.rpc.get_foo()

        print("stopping all services gracefully")
        runner.stop()
        print("services have stopped")

        assert date == datetime.date.today().isoformat()
        assert binary_number == '0b101110'
        assert foo == 'foo'
