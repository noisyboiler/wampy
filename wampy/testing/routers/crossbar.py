import atexit
import os
import signal
import socket
import subprocess

from wampy.networking.connections.tcp import TCPConnection
from wampy.constants import DEALER
from wampy.exceptions import ConnectionError
from wampy.interfaces import Peer
from wampy.logger import get_logger


logger = get_logger('examples.peers.routers.crossbar')


class Crossbar(Peer):

    def shutdown(self, pid):
        os.kill(pid, signal.SIGKILL)

    def wait_for_successful_connection(self, timeout=7):
        connection = TCPConnection()

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
        # starts the process from the root of the test namespace
        proc = subprocess.Popen([
            'crossbar', 'start', '--cbdir', './',
            '--config', './wampy/testing/routers/config.json',
        ])

        atexit.register(self.shutdown, proc.pid)
        logger.info('waiting for router connection....')
        self.wait_for_successful_connection()
        logger.info('%s router is up and running', self.name)
        return True
