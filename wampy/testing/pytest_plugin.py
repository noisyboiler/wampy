# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
import logging
import os
import psutil
import signal
import sys
import subprocess
from time import sleep

import colorlog
import pytest

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.errors import ConnectionError
from wampy.peers.clients import Client
from wampy.peers.routers import Crossbar
from wampy.session import Session
from wampy.transports import WebSocket


logger = logging.getLogger('wampy.testing')

logging_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
}


class PytestConfigurationError(Exception):
    pass


def pytest_addoption(parser):
    parser.addoption(
        '--logging-level',
        type=str,
        action='store',
        dest='logging_level',
        help='configure the logging level',
    )

    parser.addoption(
        '--file-logging',
        type=bool,
        action='store',
        dest='file_logging',
        help='optionally log to file',
        default=False,
    )


def add_file_logging():
    root = logging.getLogger()
    fhandler = logging.FileHandler(filename='test-runner-log.log', mode='a')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fhandler.setFormatter(formatter)
    root.addHandler(fhandler)
    root.setLevel(logging.DEBUG)


def pytest_configure(config):
    if config.option.logging_level is None:
        logging_level = logging.INFO
    else:
        logging_level = config.option.logging_level
        if logging_level not in logging_level_map:
            raise PytestConfigurationError(
                '{} not a recognised logging level'.format(logging_level)
            )
        logging_level = logging_level_map[logging_level]

    sh = colorlog.StreamHandler()
    sh.setLevel(logging_level)
    formatter = colorlog.ColoredFormatter(
        "%(white)s%(name)s %(reset)s %(log_color)s%"
        "(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    sh.setFormatter(formatter)
    root = logging.getLogger()
    # remove the default streamhandler
    handler = next(
        (
            handler for handler in root.handlers if
            isinstance(handler, logging.StreamHandler)
        ), None
    )
    if handler:
        index = root.handlers.index(handler)
        root.handlers.pop(index)
    # and add our fancy coloured one
    root.addHandler(sh)

    if config.option.file_logging is True:
        add_file_logging()


def find_processes(process_name):
    ps = subprocess.Popen(
        "ps -eaf | pgrep " + process_name, shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read()
    ps.stdout.close()
    ps.wait()

    return output


def get_process_ids():
    pids = []
    pids.extend([
        o for o in
        find_processes("crossbar-controller").decode().split('\n') if o
    ])
    pids.extend([
        o for o in
        find_processes("crossbar-worker").decode().split('\n') if o
    ])

    return pids


def assert_not_running(crossbar):
    try:
        crossbar.try_connection()
    except ConnectionError:
        pass
    else:
        sys.exit(
            "Crossbar is already running with unknown configuration, "
            "meaning the tests cannot reliably run - aborting!"
        )


def kill(pid):
    process = psutil.Process(pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()


def kill_crossbar(try_again=True):
    pids = get_process_ids()
    if pids and try_again is True:
        logger.warning(
            "Crossbar.io did not stop when sig term issued! "
            "Will try again."
        )

    for pid_as_str in pids:
        try:
            pid = os.getpgid(int(pid_as_str))
        except OSError:
            continue

        logger.warning("OS sending SIGTERM to crossbar pid: %s", pid)

        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:  # anything Twisted raises
            logger.exception(
                "Failed to terminate router process: %s", pid
            )

            try:
                os.waitpid(pid, options=os.WNOHANG)
            except OSError:
                pass

            try:
                os.kill(pid, signal.SIGKILL)
            except Exception as exc:
                if "No such process" in str(exc):
                    continue
                logger.exception(
                    "Failed again to terminate router process: %s", pid)

    pids = get_process_ids()
    if pids and try_again is True:
        logger.warning('try one more time to shutdown Crossbar')
        sleep(5)
        kill_crossbar(try_again=False)
    elif pids and try_again is False:
        logger.error("Failed to shutdown all router processes")


class ConfigurationError(Exception):
    pass


@pytest.yield_fixture
def url():
    return "ws://localhost:8080"


@pytest.yield_fixture
def router(config_path, url):
    logger.info('config for test run: %s', config_path)
    logger.info('url for test run: %s', url)

    crossbar = Crossbar(
        url=url,
        config_path=config_path,
        crossbar_directory='./',
    )

    assert_not_running(crossbar)
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


@pytest.yield_fixture
def client(router):
    with Client(router=router) as client:
        yield client


atexit.register(kill_crossbar)
