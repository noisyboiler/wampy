import json
import logging
import os
import signal
import socket
import subprocess
import sys
from contextlib import closing
from time import time as now

import colorlog
import eventlet
import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.networking.connection import WampConnection

from wampy.errors import ConnectionError
from wampy.registry import Registry


logger = logging.getLogger('wampy.testing')

logging_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
}


class ConfigurationError(Exception):
    pass


class PytestConfigurationError(Exception):
    pass


class TCPConnection(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))


def pytest_configure(config):
    if config.option.logging_level is None:
        logging_level = logging.INFO
    else:
        logging_level = config.option.logging_level
        if logging_level not in logging_level_map:
            raise PytestConfigurationError(
                '{} not a recognised logging level'.format(logging_level)
            )
        logging_level = logging_level_map[logging_level]

    sh = colorlog.StreamHandler()
    sh.setLevel(logging_level)
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


class Crossbar(object):
    """ Wrapper around a Crossbar.io CrossBar instance described by
    ``Crossbar.config``.

    """

    def __init__(
            self, host, port, config_path, crossbar_directory):

        with open(config_path) as data_file:
            config_data = json.load(data_file)

        self.config = config_data
        self.config_path = config_path
        self.crossbar_directory = crossbar_directory

        self.name = "Test Runner Crossbar"
        self.host = host
        self.port = port
        self.realms = self.config['workers'][0]['realms']
        self.roles = self.realms[0]['roles']

        self.proc = None

    def _wait_until_ready(self, timeout=7, raise_if_not_ready=True):
        # we're only ready when it's possible to connect to the CrossBar
        # over TCP - so let's just try it.
        connection = TCPConnection(host=self.host, port=self.port)
        end = now() + timeout

        ready = False

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    raise ConnectionError(
                        'Failed to connect to CrossBar: {}:{}'.format(
                            self.host, self.port)
                    )
                else:
                    return ready

            try:
                connection.connect()
            except socket.error:
                pass
            else:
                ready = True

        return ready

    def start(self):
        """ Start Crossbar.io in a subprocess.
        """
        # will attempt to connect or start up the CrossBar
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        cmd = [
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ]

        self.proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        self._wait_until_ready()

    def stop(self):
        logger.info('sending SIGTERM to %s', self.proc.pid)

        try:
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except Exception as exc:
            logger.exception(exc)
            logger.warning('could not kill process group')

            try:
                self.proc.kill()
            except:
                logger.execption('Failed to kill parent')
                sys.exit()
            else:
                logger.info('killed parent process instead')

        # let the shutdown happen
        eventlet.sleep(1)
        logger.info('crossbar shut down')

        Registry.clear()
        logger.info('registry cleared')


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
    check_socket(DEFAULT_HOST, DEFAULT_PORT)

    crossbar = Crossbar(
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        config_path='./test/crossbar.config.json',
        crossbar_directory='./',
    )

    crossbar.start()

    yield crossbar

    crossbar.stop()


@pytest.fixture
def connection(CrossBar):
    connection = WampConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection
