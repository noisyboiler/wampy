import atexit
import os
import signal
import socket
import subprocess

from wampy.networking.connections.tcp import TCPConnection
from wampy.constants import DEALER, DEFAULT_HOST, DEFAULT_PORT
from wampy.exceptions import ConnectionError
from wampy.interfaces import Peer
from wampy.logger import get_logger
from wampy.registry import PeerRegistry


logger = get_logger('wampy.testing.routers.crossbar')


class Crossbar(Peer):

    @property
    def config(self):
        return PeerRegistry.config_registry[self.name]

    @property
    def router_name(self):
        return self.config['name']

    @property
    def realm(self):
        return self.config['realm']

    @property
    def roles(self):
        return self.config['roles']

    def shutdown(self, pid):
        os.kill(pid, signal.SIGKILL)

    def wait_for_successful_connection(self, timeout=7):
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


class CrossbarDealer(Crossbar):

    @property
    def name(self):
        return 'Crossbar'

    def role(self):
        return DEALER

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
        self.wait_for_successful_connection()
        logger.info('%s router is up and running', self.name)
        return True
