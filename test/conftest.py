import eventlet
import pytest

from wampy.logger import get_logger
from wampy.networking.connections.wamp import WampConnection
from wampy.registry import PeerRegistry
from wampy.session import Session

from . routers.crossbar import CrossbarDealer
from . servers.http import start_pong_server


logger = get_logger('pywamp.test.conftest')


@pytest.fixture
def basic_profile_router():
    PeerRegistry.register_peer(CrossbarDealer)


@pytest.fixture
def session():
    _session = Session(name="test runner client")
    _session.begin()
    return _session


@pytest.fixture
def connection():
    connection = WampConnection(host='localhost', port=8080)
    connection.connect()
    handshake = connection._read_handshake_response()
    status, headers = handshake

    assert status == 101  # websocket success status
    assert headers['upgrade'] == 'websocket'

    return connection


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
