import logging

import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.peers.routers import Crossbar
from wampy.session import Session
from wampy.transports.websocket.connection import WampWebSocket as WebSocket


logger = logging.getLogger('wampy.testing')


class ConfigurationError(Exception):
    pass


@pytest.yield_fixture
def router():
    crossbar = Crossbar(
        config_path='./wampy/testing/configs/crossbar.config.ipv4.json',
        crossbar_directory='./',
    )

    crossbar.start()

    yield crossbar

    crossbar.stop()


@pytest.fixture
def connection(router):
    connection = WebSocket(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.fixture
def session_maker(router, connection):

    def maker(client, transport=connection):
        return Session(
            client=client, router=router, transport=transport,
        )

    return maker
