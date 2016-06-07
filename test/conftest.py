import eventlet
import pytest

from wampy.constants import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_REALM, DEFAULT_ROLES)
from wampy.logger import get_logger
from wampy.networking.connections.wamp import WampConnection
from wampy.services import ServiceRunner
from wampy.testing.routers.crossbar import Crossbar
from wampy.testing.servers.http import start_pong_server


logger = get_logger('wampy.test.conftest')


@pytest.yield_fixture
def router():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )

    crossbar.start()
    assert crossbar.started is True

    yield crossbar

    crossbar.stop()
    assert crossbar.started is False


@pytest.fixture
def connection(router):
    connection = WampConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.yield_fixture
def service_runner():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )
    crossbar.start()

    runner = ServiceRunner(
        router=crossbar,
        realm=DEFAULT_REALM,
        roles=DEFAULT_ROLES,
    )
    runner.start()

    logger.info('started the service runner: "%s"', id(runner))

    yield runner

    runner.stop()


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
