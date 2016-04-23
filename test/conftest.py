import eventlet
import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.logger import get_logger
from wampy.networking.connections.wamp import WampConnection
from wampy.testing.routers.crossbar import Crossbar
from wampy.testing.servers.http import start_pong_server
from wampy.waas import ServiceRunner


logger = get_logger('pywamp.test.conftest')


@pytest.yield_fixture
def router():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )

    crossbar.start()
    assert crossbar.pid is not None

    yield crossbar

    crossbar.stop()
    assert crossbar.pid is None


@pytest.fixture
def connection(router):
    connection = WampConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.yield_fixture
def service_runner():
    runner = ServiceRunner()
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )

    runner.register_router(crossbar)
    runner.start()

    yield runner

    runner.stop()

    assert runner.peer is None


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
