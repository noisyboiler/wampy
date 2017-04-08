import logging

import colorlog
import pytest

from wampy.peers.clients import Client

logging_level_map = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
}


@pytest.fixture(autouse=True)
def config_path():
    return './wampy/testing/configs/crossbar.config.ipv4.json'


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
    root.addHandler(sh)

    if config.option.file_logging is True:
        add_file_logging()


def add_file_logging():
    root = logging.getLogger()
    fhandler = logging.FileHandler(filename='test-runner-log.log', mode='a')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fhandler.setFormatter(formatter)
    root.addHandler(fhandler)
    root.setLevel(logging.DEBUG)


@pytest.yield_fixture
def client(router):
    with Client(router=router) as client:
        yield client
