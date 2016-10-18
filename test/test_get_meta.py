import datetime

import pytest

from wampy.peers.clients import ServiceBase as WampClient
from wampy.roles.callee import register_procedure


class Service(WampClient):

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

    @register_procedure(invocation_policy="roundrobin")
    def get_todays_date(self):
        return datetime.datetime.today()

    @register_procedure(invocation_policy="roundrobin")
    def get_squared(self, number):
        return number * number


class TestGetMetaFromClients(object):

    @pytest.yield_fixture
    def services(self, router):
        names = [
            "orion", "pluto", "saturn", "neptune", "earth",
        ]

        service_cluster = [Service(name=name) for name in names]

        for service in service_cluster:
            service.start()

        yield

        for service in service_cluster:
            service.stop()

    def test_get_meta(self, services):
        stand_alone = WampClient(name="enquirer")

        expected_meta = {
            'enquirer': {
                'name': 'enquirer',
                'registrations': ['get_meta'],
                'subscriptions': []
            },
            'orion': {
                'name': 'orion',
                'registrations': [
                    'get_meta', 'get_squared', 'get_todays_date'
                ],
                'subscriptions': []
            },
            'pluto': {
                'name': 'pluto',
                'registrations': [
                    'get_meta', 'get_squared', 'get_todays_date'
                ],
                'subscriptions': []
            },
            'saturn': {
                'name': 'saturn',
                'registrations': [
                    'get_meta', 'get_squared', 'get_todays_date'
                ],
                'subscriptions': []
            },
            'neptune': {
                'name': 'neptune',
                'registrations': [
                    'get_meta', 'get_squared', 'get_todays_date'
                ],
                'subscriptions': []
            },
            'earth': {
                'name': 'earth',
                'registrations': [
                    'get_meta', 'get_squared', 'get_todays_date'
                ],
                'subscriptions': []
            },
        }

        with stand_alone as client:
            collection = client.collect_client_meta_data()

        assert collection == expected_meta
