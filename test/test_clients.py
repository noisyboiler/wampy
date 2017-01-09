import datetime
from datetime import date

import eventlet
import pytest

from wampy.peers.clients import DefaultClient as Client
from wampy.roles.callee import register_rpc


class DateService(Client):

    @register_rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class HelloService(Client):

    @register_rpc
    def say_hello(self, name):
        message = "Hello {}".format(name)
        return message

    @register_rpc
    def say_greeting(self, name, greeting="hola"):
        message = "{greeting} to {name}".format(
            greeting=greeting, name=name)
        return message


class BinaryNumberService(Client):

    @register_rpc
    def get_binary(self, integer):
        """ Return the binary format for a given base ten integer.
        """
        result = bin(integer)
        return result


@pytest.yield_fixture
def date_service(router):
    with DateService():
        yield


@pytest.yield_fixture
def hello_service(router):
    with HelloService():
        yield


@pytest.yield_fixture
def binary_number_service(router):
    with BinaryNumberService():
        yield


@pytest.fixture
def client_instances(router):
    client_ids = [
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

    client_instances = make_service_clients(router, client_ids)
    return client_instances


@pytest.yield_fixture
def clients(client_instances):
    for client in client_instances:
        client.start()

    yield client_instances
    for client in client_instances:
        client.stop()


def make_service_clients(router, ids):
    clients = []
    for id_ in ids:
        clients.append(Client(id=id_))

    return clients


def test_client_connects_to_router(router):

    class MyClient(Client):
        pass

    client = MyClient()

    assert client.session.id is None

    client.start()

    session = client.session
    assert session.id is not None
    assert session.client is client

    client.stop()

    assert client.session.id is None


def test_can_start_two_clients(router):

    class MyClient(Client):
        pass

    app_one = MyClient()
    app_one.start()
    assert app_one.session.id

    app_two = MyClient()
    app_two.start()
    assert app_two.session.id

    app_one.stop()
    app_two.stop()

    assert app_one.session.id is None
    assert app_two.session.id is None


def test_call_with_no_args_or_kwargs(date_service, router):
    client = Client()
    with client:
        response = client.rpc.get_todays_date()

    today = date.today()

    assert response == today.isoformat()


def test_call_with_args_but_no_kwargs(hello_service, router):
    caller = Client()
    with caller:
        response = caller.rpc.say_hello("Simon")

    assert response == "Hello Simon"


def test_call_with_no_args_but_a_default_kwarg(hello_service, router):
    caller = Client()
    with caller:
        response = caller.rpc.say_greeting("Simon")

    assert response == "hola to Simon"


def test_call_with_no_args_but_a_kwarg(hello_service, router):
    caller = Client()
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
        client_id = client.id
        required_request = required_client_request_map[client_id]
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
