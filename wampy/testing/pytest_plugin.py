import atexit
import logging
import os
import signal

import subprocess

import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.peers.routers import Crossbar
from wampy.session import Session
from wampy.transports.websocket.connection import WampWebSocket as WebSocket


logger = logging.getLogger('wampy.testing')


def find_processes(process_name):
    ps = subprocess.Popen(
        "ps -eaf | pgrep " + process_name, shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    return output


def kill_crossbar():
    output = find_processes("crossbar")
    pids = [o for o in output.decode().split('\n') if o]
    if pids:
        logger.error(
            "Crossbar.io did not stop when sig term issued!"
        )

    for pid in pids:
        logger.warning("OS sending SIGTERM to crossbar pid: %s", pid)
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            logger.error("Failed to terminate router process again: %s", pid)
            try:
                os.kill(int(pid), signal.SIGKILL)
            except Exception as exc:
                if "No such process" in str(exc):
                    return
                logger.exception("Failed to shutdown router")
                raise


class ConfigurationError(Exception):
    pass


@pytest.yield_fixture
def router(config_path):
    crossbar = Crossbar(
        config_path=config_path,
        crossbar_directory='./',
    )

    crossbar.start()

    yield crossbar

    crossbar.stop()
    kill_crossbar()


@pytest.fixture
def connection(router):
    connection = WebSocket(host=DEFAULT_HOST, port=DEFAULT_PORT)
    connection.connect()

    assert connection.status == 101  # websocket success status
    assert connection.headers['upgrade'] == 'websocket'

    return connection


@pytest.fixture
def session_maker(router, connection):

    def maker(client, transport=connection):
        return Session(
            client=client, router=router, transport=transport,
        )

    return maker


atexit.register(kill_crossbar)
