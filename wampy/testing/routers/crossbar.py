import atexit
import json
import psutil
import socket
import subprocess

from wampy.networking.connections.tcp import TCPConnection
from wampy.constants import DEALER, DEFAULT_HOST, DEFAULT_PORT
from wampy.exceptions import ConnectionError
from wampy.logger import get_logger

from . router import Router


logger = get_logger('wampy.testing.routers.crossbar')


class Crossbar(Router):

    def __init__(self, host, config_path, crossbar_directory=None):
        super(Crossbar, self).__init__(host, config_path)
        self.crossbar_directory = crossbar_directory
        self.pid = None

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
            with open(self.config_path) as data_file:
                data = json.load(data_file)

            self._config = data

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
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        proc = subprocess.Popen([
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ])

        atexit.register(self.stop)
        logger.info('waiting for router connection....')
        self._wait_until_ready()

        self.pid = proc.pid
        logger.info('%s router is up and running', self.name)
        return True

    def stop(self):
        if self.pid is None:
            return
        parent = psutil.Process(self.pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

        self.pid = None
