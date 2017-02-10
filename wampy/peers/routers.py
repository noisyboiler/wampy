import json
import logging
import os
import signal
import socket
import subprocess
import sys
from time import time as now, sleep

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.errors import ConnectionError

logger = logging.getLogger('wampy.peers.routers')


class TCPConnection(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((self.host, self.port))


class Crossbar(object):

    def __init__(
            self, host=DEFAULT_HOST, port=DEFAULT_PORT,
            realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
            config_path=None, crossbar_directory=None,
            certificate=None,
    ):

        self.host = host
        self.port = port
        self.certificate = certificate

        if config_path:
            with open(config_path) as data_file:
                config_data = json.load(data_file)
            self.config = config_data
            self.config_path = config_path
            self.realm = self.config['workers'][0]['realms'][0]
            self.roles = self.realm['roles']
        else:
            self.config = None
            self.realm = realm
            self.roles = roles

        self.crossbar_directory = crossbar_directory

        self.proc = None

    @property
    def can_use_tls(self):
        return bool(self.certificate)

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
