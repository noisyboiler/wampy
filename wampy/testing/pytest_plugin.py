import json
import logging
import os
import signal
import socket
import subprocess
import sys
from contextlib import closing
from time import time as now, sleep

import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_REALM
from wampy.errors import ConnectionError
from wampy.networking.connection import WampWebConnection
from wampy.session import Session


logger = logging.getLogger('wampy.testing')


class ConfigurationError(Exception):
    pass


class TCPConnection(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))


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
        sleep(2)
        logger.info('crossbar shut down')


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
        config_path='./test/crossbar.config.json',
        crossbar_directory='./',
    )

    check_socket(DEFAULT_HOST, DEFAULT_PORT)
    crossbar.start()

    yield crossbar

    crossbar.stop()
    check_socket(DEFAULT_HOST, DEFAULT_PORT)


@pytest.fixture
def connection(router):
    connection = WampWebConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.fixture
def session_maker(router, connection):

    def maker(client, realm=DEFAULT_REALM, transport=connection):
        return Session(
            client=client, router=router,
            realm=realm, transport=transport,
        )

    return maker
