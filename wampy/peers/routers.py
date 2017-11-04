# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import logging
import os
import socket
import subprocess
from socket import error as socket_error
from time import time as now, sleep

from tenacity import retry, stop_after_attempt, wait_fixed

from wampy.errors import ConnectionError, WampyError
from wampy.mixins import ParseUrlMixin

logger = logging.getLogger('wampy.peers.routers')


class Router(ParseUrlMixin):
    def __init__(self, url, cert_path=None, ipv=4):
        self.url = url
        self.certificate = cert_path
        self.ipv = ipv
        self.parse_url()


class Crossbar(ParseUrlMixin):

    def __init__(
        self, config_path="./crossbar/config.json", crossbar_directory=None,
    ):

        with open(config_path) as data_file:
            config_data = json.load(data_file)

        self.config = config_data
        self.config_path = config_path
        config = self.config['workers'][0]

        self.realm = config['realms'][0]
        self.roles = self.realm['roles']

        if len(config['transports']) > 1:
            raise WampyError(
                "Only a single websocket transport is supported by Wampy, "
                "sorry"
            )

        self.transport = config['transports'][0]
        self.url = self.transport.get("url")
        if self.url is None:
            raise WampyError(
                "The ``url`` value is required by Wampy. "
                "Please add to your configuration file. Thanks."
            )

        self.ipv = self.transport['endpoint'].get("version", None)
        if self.ipv is None:
            logger.warning(
                "defaulting to IPV 4 because neither was specified."
            )
            self.ipv = 4

        self.parse_url()

        self.websocket_location = self.resource

        self.crossbar_directory = crossbar_directory

        try:
            self.certificate = self.transport['endpoint']['tls']['certificate']
        except KeyError:
            self.certificate = None

        self.proc = None
        self.started = False

    @property
    def can_use_tls(self):
        return bool(self.certificate)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _wait_until_ready(self, timeout=5, raise_if_not_ready=True):
        # we're only ready when it's possible to connect to the CrossBar
        # over TCP - so let's just try it.
        end = now() + timeout
        ready = False

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    raise ConnectionError(
                        'Failed to connect to CrossBar over IPV{}: '
                        '{}:{}'.format(
                            self.ipv, self.host, self.port,
                        )
                    )
                else:
                    return ready

            try:
                self.try_connection()
            except ConnectionError:
                pass
            else:
                ready = True

        return ready

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    def start(self):
        """ Start Crossbar.io in a subprocess.
        """
        if self.started is True:
            raise WampyError("Router already started")

        # will attempt to connect or start up the CrossBar
        crossbar_config_path = self.config_path
        cbdir = self.crossbar_directory

        # starts the process from the root of the test namespace
        cmd = [
            'crossbar', 'start',
            '--cbdir', cbdir,
            '--config', crossbar_config_path,
        ]

        logger.debug('starting Crosbar"%s"', cmd)
        self.proc = subprocess.Popen(cmd, preexec_fn=os.setsid)
        logger.info('waiting for Crosbar: "%s"', self.proc)
        self._wait_until_ready()
        logger.debug(
            "Crosbar.io is ready for connections on %s (IPV%s)",
            self.url, self.ipv
        )

        self.started = True

    def stop(self):
        logger.warning("stopping crossbar")

        # handles gracefully a user already terminated server, the auto
        # termination failing and killing the process to ensure has died.

        try:
            self.proc.terminate()
        except OSError as exc:
            if "no such process" in str(exc).lower():
                logger.warning("process died already: %s", self.proc)
                return
            logger.warning("process %s did not terminate", self.proc)
        else:
            # wait for a graceful shutdown
            logger.info("sleeping while Crossbar shuts down")
            sleep(2)

        if self.proc.stdout:
            logger.info('crossbar process output: "%s"', self.proc.stdout)

        if self.proc.stderr:
            logger.error('crossbar process errors: "%s"', self.proc.stderr)

        if self.proc.poll() is None:
            logger.warning('crossbar has NOT shut down, sorry.')

        self.started = False

    def try_connection(self):
        if self.ipv == 4:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                _socket.connect((self.host, self.port))
            except socket_error:
                raise ConnectionError("Could not connect")

        elif self.ipv == 6:
            _socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

            try:
                _socket.connect(("::", self.port))
            except socket_error:
                raise ConnectionError("Could not connect")

        else:
            raise WampyError(
                "unknown IPV: {}".format(self.ipv)
            )

        _socket.shutdown(socket.SHUT_RDWR)
        _socket.close()
