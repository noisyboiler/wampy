import datetime
from datetime import date

import eventlet
import pytest

from wampy import WebApplication
from wampy.roles.callee import register_rpc


class Service(WebApplication):

    @register_rpc(invocation_policy="roundrobin")
    def get_todays_date(self):
        return datetime.datetime.today()

    @register_rpc(invocation_policy="roundrobin")
    def get_squared(self, number):
        return number * number


class DateService(WebApplication):

    @register_rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(WebApplication):

    @register_rpc
    def say_hello(self, name):
        message = "Hello {}".format(name)
        return message

    @register_rpc
    def say_greeting(self, name, greeting="hola"):
        message = "{greeting} to {name}".format(
            greeting=greeting, name=name)
        return message


class BinaryNumberService(WebApplication):

    @register_rpc
    def get_binary(self, integer):
        """ Return the binary format for a given base ten integer.
        """
        result = bin(integer)
        return result


@pytest.yield_fixture
def date_service(router):
    with DateService(name="date service"):
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService(name="hello service"):
        yield


@pytest.yield_fixture
def binary_number_service(router):
    with BinaryNumberService(name="Binary Number Service"):
        yield


@pytest.fixture
def client_instances(router):
    client_names = [
        'binary_number_consumer_001',
        'binary_number_consumer_002',
        'binary_number_consumer_003',
        'binary_number_consumer_004',
        'binary_number_consumer_005',
        'binary_number_consumer_006',
        'binary_number_consumer_007',
        'binary_number_consumer_008',
        'binary_number_consumer_009',
        'binary_number_consumer_010',
    ]

    client_instances = make_service_clients(router, client_names)
    return client_instances


@pytest.yield_fixture
def clients(client_instances):
    for client in client_instances:
        client.start()

    yield client_instances
    for client in client_instances:
        client.stop()


def make_service_clients(router, names):
    clients = []
    for name in names:
        clients.append(WebApplication(name=name))

    return clients


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
        stand_alone = WebApplication(name="enquirer")

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


def test_call_with_no_args_or_kwargs(date_service, router):
    client = WebApplication(name="just a client")
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = WebApplication(name="just a client")
    with caller:
        response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = WebApplication(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = WebApplication(name="Caller")
    with caller:
        response = caller.rpc.say_greeting("Simon", greeting="goodbye")

    assert response == "goodbye to Simon"


def test_concurrent_client_calls(binary_number_service, clients):
    required_client_request_map = {
        'binary_number_consumer_001': 1,
        'binary_number_consumer_002': 30,
        'binary_number_consumer_003': 501,
        'binary_number_consumer_004': 499,
        'binary_number_consumer_005': 498,
        'binary_number_consumer_006': 1010,
        'binary_number_consumer_007': 1001,
        'binary_number_consumer_008': 1,
        'binary_number_consumer_009': 9999,
        'binary_number_consumer_010': 001,
    }

    # build test data
    test_data = {}
    for client in clients:
        client_name = client.name
        required_request = required_client_request_map[client_name]
        test_data[client] = required_request

    expected_results_map = {
        'binary_number_consumer_001': '0b1',
        'binary_number_consumer_002': '0b11110',
        'binary_number_consumer_003': '0b111110101',
        'binary_number_consumer_004': '0b111110011',
        'binary_number_consumer_005': '0b111110010',
        'binary_number_consumer_006': '0b1111110010',
        'binary_number_consumer_007': '0b1111101001',
        'binary_number_consumer_008': '0b1',
        'binary_number_consumer_009': '0b10011100001111',
        'binary_number_consumer_010': '0b1',
    }

    expected_results = expected_results_map.values()

    requests = test_data.items()

    def fetch_binary_form_of_number(request):
        client, base_ten_number = request
        binary_number = client.rpc.get_binary(
            integer=base_ten_number)
        return binary_number

    pool = eventlet.GreenPool()
    results = []
    for result in pool.imap(
            fetch_binary_form_of_number, requests
    ):

        results.append(result)

    assert sorted(expected_results) == sorted(results)
