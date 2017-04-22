import pytest

from wampy.peers.clients import Client


@pytest.fixture(autouse=True)
def config_path():
    return './wampy/testing/configs/crossbar.config.ipv4.json'


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


@pytest.yield_fixture
def client(router):
    with Client(router=router) as client:
        yield client
