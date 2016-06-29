import logging

import colorlog
import eventlet
import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.networking.connections.wamp import WampConnection
from wampy.testing.routers.crossbar import Crossbar
from wampy.testing.servers.http import start_pong_server


logger = logging.getLogger('wampy.testing')

logging_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
}


class PytestConfigurationError(Exception):
    pass


def pytest_configure(config):
    if config.option.logging_level:
        logging_level = config.option.logging_level
        if logging_level not in logging_level_map:
            raise PytestConfigurationError(
                '{} not a recognised logging level'.format(logging_level)
            )

        sh = colorlog.StreamHandler()
        sh.setLevel(logging_level_map[logging_level])
        formatter = colorlog.ColoredFormatter(
            "%(white)s%(name)s %(reset)s %(log_color)s%"
            "(levelname)-8s%(reset)s %(blue)s%(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
            )

        sh.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(sh)


def pytest_addoption(parser):
    parser.addoption(
        '--logging-level',
        type=str,
        action='store',
        dest='logging_level',
        help='configure the logging level',
    )


@pytest.yield_fixture
def router():
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )

    crossbar.start()

    yield crossbar

    crossbar.stop()


@pytest.fixture
def connection(router):
    connection = WampConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

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
