import atexit
import json
import os
import signal
import socket
import subprocess

from wampy.networking.connections.tcp import TCPConnection
from wampy.constants import DEALER, DEFAULT_HOST, DEFAULT_PORT
from wampy.exceptions import ConnectionError
from wampy.logger import get_logger
from wampy.registry import PeerRegistry

from . router import Router


logger = get_logger('wampy.testing.routers.crossbar')


class Crossbar(Router):

    @property
    def name(self):
        return 'crossbar'

    @property
    def role(self):
        return DEALER

    @property
    def config(self):
        try:
            self._config
        except AttributeError:
            raw_config = PeerRegistry.config_registry[self.name]
            config_path = raw_config['local_configuration']
            with open(config_path) as data_file:
                data = json.load(data_file)

            self._config = data
            self._config.update(raw_config)

        return self._config

    @property
    def port(self):
        # this is loaded with assumptions and requires proper consideration.
        return self.config['workers'][0]['transports'][0]['endpoint']['port']

    def _wait_until_ready(self, timeout=7):
        # we're only ready when it's possible to connect over TCP to us
        connection = TCPConnection(host=DEFAULT_HOST, port=DEFAULT_PORT)

        from time import time as now
        end = now() + timeout

        waiting = True
        while waiting:
            timeout = end - now()
            if timeout < 0:
                raise ConnectionError(
                    'Failed to connect to router'
                )

            try:
                connection.connect()
            except socket.error:
                pass
            else:
                waiting = False

    def start(self):
        crossbar_config_path = self.config['local_configuration']
        cbdir = self.config['cbdir']

        # starts the process from the root of the test namespace
        proc = subprocess.Popen([
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ])

        atexit.register(self.shutdown, proc.pid)
        logger.info('waiting for router connection....')
        self._wait_until_ready()
        logger.info('%s router is up and running', self.name)
        return True

    def shutdown(self, pid):
        os.kill(pid, signal.SIGKILL)
