import json
import socket
import os
import signal
import subprocess
from time import time as now

from wampy.networking.connections.tcp import TCPConnection
from wampy.constants import DEALER
from wampy.exceptions import ConnectionError
from wampy.logger import get_logger

from ... registry import Registry
from . router import Router


logger = get_logger('wampy.testing.routers.crossbar')


class Crossbar(Router):
    """ Wrapper around a Crossbar.io router instance described
    by ``Crossbar.config``.

    """
    def __init__(self, host, config_path, crossbar_directory=None):
        super(Crossbar, self).__init__(host, config_path)

        self.host = host
        self.crossbar_directory = crossbar_directory
        self.proc = None
        self._router_running = None

    @property
    def name(self):
        return 'Crossbar'

    @property
    def role(self):
        return DEALER

    @property
    def router(self):
        return self

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
    def started(self):
        return self._router_running

    @property
    def port(self):
        # this is loaded with assumptions and requires proper consideration.
        return self.config['workers'][0]['transports'][0]['endpoint']['port']

    def handle_message(self):
        pass

    def wait_until_ready(self, timeout=7, raise_if_not_ready=True):
        logger.info('create TCPConnection')
        # we're only ready when it's possible to connect over TCP to us
        connection = TCPConnection(host=self.host, port=self.port)
        end = now() + timeout

        ready = False
        logger.info('wait until ready')

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    logger.exception('%s unable to connect', self.name)
                    raise ConnectionError(
                        'Failed to connect to router'
                    )
                else:
                    return ready

            try:
                connection.connect()
            except socket.error:
                logger.error('failed to connect')
            else:
                ready = True

        return ready

    def start(self):
        """ Start Crossbar.io in a subprocess.
        """
        if self.started is True:
            logger.info('%s already started', self.name)
            return

        # will attempt to connect or start up the router
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        cmd = [
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ]

        if self.started is None or self.started is False:
            logger.info('%s not started', self.name)
            logger.info('%s router starting up', self.name)
            self.proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        logger.info('waiting for router connection....')
        self.wait_until_ready()
        logger.info('ready')

        self._router_running = True

        logger.info(
            '%s router is up and running with PID "%s"',
            self.name, self.proc.pid
        )

    def stop(self):
        logger.info('attempting to shut down crossbar')

        try:
            logger.info('sending SIGTERM to %s', self.proc.pid)
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except Exception as exc:
            logger.exception(exc)
            logger.warning('could not kill process group')
            self.proc.kill()
            logger.info('killed parent process instead')

        # give the Router a chance to shut down
        from time import sleep
        sleep(1)

        self._router_running = False

        logger.info('crossbar shut down')
        Registry.clear()
        logger.info('registry cleared')
