import atexit
import json
import logging
import os
import signal
import socket
import subprocess
from socket import error as socket_error
from time import time as now, sleep
from urlparse import urlsplit

from wampy.errors import ConnectionError, WampyError

logger = logging.getLogger('wampy.peers.routers')


def find_processes(process_name):
    ps = subprocess.Popen(
        "ps -eaf | pgrep " + process_name, shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    return output


def kill_crossbar():
    output = find_processes("crossbar")
    pids = [o for o in output.split('\n') if o]
    for pid in pids:
        logger.warning("sending SIGTERM to crossbar pid: %s", pid)
        try:
            os.kill(int(pid), signal.SIGTERM)
        except Exception:
            logger.exception("SIGTERM failed - try and kill process group")
            try:
                os.killpg(os.getpgid(int(pid)), signal.SIGTERM)
            except:
                logger.exception('Failed to kill process: %s', pid)


def finally_kill_crossbar():
    output = find_processes("crossbar")
    if output:
        logger.warning("test run ended: sending SIGTERM")
        # give any other threads another chance to finish
        sleep(2)
        try:
            kill_crossbar()
        except:
            logger.warning(
                "failed to kill crossbar at end of test run"
            )

atexit.register(finally_kill_crossbar)


class TCPConnection(object):
    def __init__(self, host, port, ipv):
        self.host = host
        self.port = port
        self.ipv = ipv

    def connect(self):
        if self.ipv == 4:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                _socket.connect((self.host, self.port))
            except socket_error:
                pass

        elif self.ipv == 6:
            _socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

            try:
                _socket.connect(("::", self.port))
            except socket_error:
                pass

        else:
            raise WampyError(
                "unknown IPV: {}".format(self.ipv)
            )

        _socket.shutdown(socket.SHUT_RDWR)
        _socket.close()


class Crossbar(object):

    def __init__(
        self, config_path, crossbar_directory=None, certificate=None,
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

        self._parse_url()

        self.websocket_location = self.resource

        self.crossbar_directory = crossbar_directory
        self.certificate = certificate

        self.proc = None

    @property
    def can_use_tls(self):
        return bool(self.certificate)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop()

    def _parse_url(self):
        """
        Parses a URL which must have one of the following forms:

        - ws://host[:port][path]
        - wss://host[:port][path]
        - ws+unix:///path/to/my.socket

        In the first two cases, the ``host`` and ``port``
        attributes will be set to the parsed values. If no port
        is explicitely provided, it will be either 80 or 443
        based on the scheme. Also, the ``resource`` attribute is
        set to the path segment of the URL (alongside any querystring).

        In addition, if the scheme is ``ws+unix``, the
        ``unix_socket_path`` attribute is set to the path to
        the Unix socket while the ``resource`` attribute is
        set to ``/``.
        """
        # Python 2.6.1 and below don't parse ws or wss urls properly.
        # netloc is empty.
        # See: https://github.com/Lawouach/WebSocket-for-Python/issues/59
        scheme, url = self.url.split(":", 1)

        parsed = urlsplit(url, scheme="http")
        if parsed.hostname:
            self.host = parsed.hostname
        elif '+unix' in scheme:
            self.host = 'localhost'
        else:
            raise ValueError("Invalid hostname from: %s", self.url)

        if parsed.port:
            self.port = parsed.port

        if scheme == "ws":
            if not self.port:
                self.port = 80
        elif scheme == "wss":
            if not self.port:
                self.port = 443
        elif scheme in ('ws+unix', 'wss+unix'):
            pass
        else:
            raise ValueError("Invalid scheme: %s" % scheme)

        if parsed.path:
            resource = parsed.path
        else:
            resource = "/"

        if '+unix' in scheme:
            self.unix_socket_path = resource
            resource = '/'

        if parsed.query:
            resource += "?" + parsed.query

        self.scheme = scheme
        self.resource = resource

    def _wait_until_ready(self, timeout=7, raise_if_not_ready=True):
        # we're only ready when it's possible to connect to the CrossBar
        # over TCP - so let's just try it.
        connection = TCPConnection(
            host=self.host, port=self.port, ipv=self.ipv)
        end = now() + timeout

        ready = False

        while not ready:
            timeout = end - now()
            if timeout < 0:
                if raise_if_not_ready:
                    raise ConnectionError(
                        'Failed to connect to CrossBar over {}: {}:{}'.format(
                            self.ipv, self.host, self.port)
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
        logger.info(
            "Crosbar.io is ready for connections on %s (IPV%s)",
            self.url, self.ipv
        )

    def stop(self):
        kill_crossbar()
        # let the shutdown happen
        sleep(2)

        output = find_processes("crossbar").strip()
        if output:
            logger.error("Crossbar is still running: %s", output)
        else:
            logger.info('crossbar shut down')
