import eventlet
import json
import os
import signal
import subprocess

from ... peers.routers import Router
from ... registry import Registry


class Crossbar(Router):
    """ Wrapper around a Crossbar.io router instance described by
    ``Crossbar.config``.

    """

    def __init__(
            self, host, port, config_path, crossbar_directory=None):

        super(Crossbar, self).__init__(host, port)

        with open(config_path) as data_file:
            config_data = json.load(data_file)

        self.config = config_data
        self.config_path = config_path
        self.crossbar_directory = crossbar_directory
        self.proc = None

    @property
    def name(self):
        return 'Crossbar.io'

    @property
    def realm(self):
        realms = self.config['workers'][0]['realms']
        # ensure our simpilfied world holds true
        assert len(realms) == 1
        # then return it
        return realms[0]['name']

    @property
    def roles(self):
        roles = self.realms[0]['roles']
        # ensure our simpilfied world holds true
        assert len(roles) == 1
        # then return it
        return roles[0]

    @property
    def session(self):
        return self._session

    def start(self):
        """ Start Crossbar.io in a subprocess.
        """
        # will attempt to connect or start up the router
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        cmd = [
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ]

        self.proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        self.logger.info('waiting for router connection....')
        self._wait_until_ready()
        self.logger.info(
            '%s router is up and running with PID "%s"',
            self.name, self.proc.pid
        )

    def stop(self):
        self.logger.info('attempting to shut down crossbar')

        try:
            self.logger.info('sending SIGTERM to %s', self.proc.pid)
            os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except Exception as exc:
            self.logger.exception(exc)
            self.logger.warning('could not kill process group')
            self.proc.kill()
            self.logger.info('killed parent process instead')

        # let the shutdown happen
        eventlet.sleep(1)

        self.logger.info('crossbar shut down')
        Registry.clear()
        self.logger.info('registry cleared')
