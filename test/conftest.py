import eventlet
import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.logger import get_logger
from wampy.networking.connections.wamp import WampConnection
from wampy.registry import PeerRegistry
from wampy.session import Session

from wampy.testing.routers.crossbar import CrossbarDealer
from wampy.testing.servers.http import start_pong_server


logger = get_logger('pywamp.test.conftest')


@pytest.fixture
def basic_profile_router():
    config = {
        'cbdir': './',
        'local_configuration': './wampy/testing/routers/config.json',
    }

    PeerRegistry.register_peer(CrossbarDealer, config)


@pytest.fixture
def connection(basic_profile_router):
    connection = WampConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.fixture
def session(connection):
    _session = Session(
        name="Test Runner WAMP Session", connection=connection)
    _session.begin()
    return _session


@pytest.yield_fixture
def http_pong_server():
    thread = eventlet.spawn(start_pong_server)

    # give the server a second to start up
    eventlet.sleep()
    yield

    while not thread.dead:
        eventlet.sleep()
        thread.kill()

    assert thread.dead
