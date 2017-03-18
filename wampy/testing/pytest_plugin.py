import logging
import socket
from contextlib import closing

import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.peers.routers import Crossbar
from wampy.session import Session
from wampy.transports.websocket.connection import WebSocket


logger = logging.getLogger('wampy.testing')


class ConfigurationError(Exception):
    pass


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) is None:
            raise ConfigurationError(
                '{}:{} not available - is crossbar already running?'.format(
                    host, port
                )
            )


@pytest.yield_fixture
def router():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        config_path='./wampy/testing/configs/crossbar.config.json',
        crossbar_directory='./',
    )

    check_socket(DEFAULT_HOST, DEFAULT_PORT)
    crossbar.start()

    yield crossbar

    crossbar.stop()
    check_socket(DEFAULT_HOST, DEFAULT_PORT)


@pytest.yield_fixture
def tls_router():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        certificate="./wampy/testing/keys/server_cert.pem",
        config_path='./wampy/testing/configs/crossbar.config.tls.json',
        crossbar_directory='./',
    )

    check_socket(DEFAULT_HOST, DEFAULT_PORT)
    crossbar.start()

    yield crossbar

    crossbar.stop()
    check_socket(DEFAULT_HOST, DEFAULT_PORT)


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
