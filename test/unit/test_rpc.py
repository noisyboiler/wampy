import eventlet
import logging
import pytest

from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.peers.clients import WampClient
from wampy.rpc import rpc


logger = logging.getLogger('test_rpc')


def make_service_clients(router, names):
    clients = []
    for name in names:
        clients.append(
            WampClient(
                name=name, router=router,
                realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
            )
        )

    return clients


class BinaryNumberService(WampClient):

    @rpc
    def get_binary(self, integer):
        """ Return the binary format for a given base ten integer.
        """
        logger.info('BinaryNumberService handling request for: "%s"', integer)
        result = bin(integer)
        logger.info('BinaryNumberService returning: "%s"', result)
        return result


@pytest.yield_fixture
def binary_number_service(router):
    with BinaryNumberService(
        name="Binary Number Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES
    ):

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
    logger.info("stopping all clients")
    for client in client_instances:
        client.stop()


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
        logger.info(
            "%s fetching binary form of %s",
            client.name, base_ten_number
        )
        binary_number = client.rpc.get_binary(
            integer=base_ten_number)
        logger.info('got binary number: %s', binary_number)
        return binary_number

    pool = eventlet.GreenPool()
    results = []
    for result in pool.imap(
            fetch_binary_form_of_number, requests
    ):

        results.append(result)

    assert sorted(expected_results) == sorted(results)
